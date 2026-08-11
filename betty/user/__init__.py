"""
An API to interact with Betty's user.
"""

from __future__ import annotations

import contextlib
import logging
import threading
from _asyncio import get_running_loop
from _queue import Empty
from abc import ABCMeta, abstractmethod
from asyncio import CancelledError, run_coroutine_threadsafe, to_thread
from collections.abc import Callable, Coroutine
from enum import IntEnum
from functools import partial
from queue import Queue
from time import sleep
from typing import TYPE_CHECKING, Final, final, overload, override

from babel import Locale
from babel import default_locale as babel_default_locale

from betty.functools import Result, ResultUnavailable, suppress
from betty.life_cycle import LifeCycle
from betty.locale import default_locale
from betty.nothing import Nothing, NothingType

if TYPE_CHECKING:
    from collections.abc import Mapping
    from contextlib import AbstractAsyncContextManager

    from betty.functools import Pipe
    from betty.localizable import ResolvableLocalizable
    from betty.localizer import Localizer
    from betty.progress import Progress


@final
class Severity(IntEnum):
    """
    User message severities.
    """

    ERROR = 1
    """
    Something went wrong and was aborted.
    """

    WARN = 2
    """
    Something may have gone wrong, or has gone wrong and Betty has recovered from it.
    """

    CONFIRM = 3
    """
    Confirm a user action.
    """

    INFO = 4
    """
    Provide additional, non-essential, related information.
    """

    DEBUG = 5
    """
    Details relevant to debugging.
    """


def log_level_to_severity(log_level: int, /) -> Severity:
    """
    Convert a :py:mod:`logging` log level to a :py:class:`betty.user.Severity`.
    """
    if log_level >= logging.ERROR:
        return Severity.ERROR
    if log_level >= logging.WARNING:
        return Severity.WARN
    if log_level >= logging.INFO:
        return Severity.INFO
    return Severity.DEBUG


severity_to_log_level: Final[Mapping[Severity | bool, int]] = {
    False: 999999999,
    Severity.ERROR: logging.ERROR,
    Severity.WARN: logging.WARNING,
    Severity.CONFIRM: logging.INFO,
    Severity.INFO: logging.INFO,
    Severity.DEBUG: 0,
    True: 0,
}
"""
Convert a :py:class:`betty.user.Severity` to a :py:mod:`logging` log level.
"""


class UserError(Exception):
    """
    A user session error.
    """


class UserTimeoutError(UserError):
    """
    The user did not respond within the given time, or at all.
    """


class User(metaclass=ABCMeta):
    """
    A user session.
    """

    default_locale: Final[Locale] = (
        Locale.parse(system_default_locale)
        if (system_default_locale := babel_default_locale())
        else default_locale
    )
    """
    The default locale for most users.
    """

    default_severity: Final[Severity | bool] = Severity.CONFIRM
    """
    The default severity for most users.
    """

    severity: Severity | bool = default_severity
    """
    The current severity.
    """

    @final
    def shows(self, severity: Severity, /) -> bool:
        """
        Check if the user currently shows messages with the given severity.
        """
        if isinstance(self.severity, bool):
            return self.severity
        return self.severity >= severity

    @final
    def logs(self, log_level: int, /) -> Severity | None:
        """
        Check if the user currently logs records with the given level.
        """
        severity = log_level_to_severity(log_level)
        return severity if self.shows(severity) else None

    @property
    @abstractmethod
    def localizer(self) -> Localizer:
        """
        The localizer.
        """

    @abstractmethod
    async def exception(self) -> None:
        """
        Send a message about an exception to the user.

        These messages have a severity of :py:attr:`betty.user.Severity.ERROR`.
        """

    @abstractmethod
    async def message(
        self, message: ResolvableLocalizable, severity: Severity, /
    ) -> None:
        """
        Send a message to the user.
        """

    @abstractmethod
    async def log(self, record: logging.LogRecord, /) -> None:
        """
        Send a log message to the user.
        """

    @abstractmethod
    def progress(
        self, message: ResolvableLocalizable, /
    ) -> AbstractAsyncContextManager[Progress]:
        """
        Send information about a progressing activity to the user.
        """

    @abstractmethod
    async def ask_confirmation(
        self, statement: ResolvableLocalizable, /, *, default: bool = False
    ) -> bool:
        """
        Ask the user to confirm a statement.

        :raises: betty.user.UserTimeoutError
        """

    @overload
    async def ask_input(
        self,
        question: ResolvableLocalizable,
        /,
        *,
        assertion: None = None,
        default: str | NothingType = Nothing,
    ) -> str:
        pass

    @overload
    async def ask_input[T](
        self,
        question: ResolvableLocalizable,
        /,
        *,
        assertion: Pipe[str, T],
        default: str | NothingType = Nothing,
    ) -> T:
        pass

    @abstractmethod
    async def ask_input(self, question, /, *, assertion=None, default=Nothing):
        """
        Ask the user to input text.

        :raises: betty.user.UserTimeoutError
        """


@final
class UserHandler(LifeCycle, logging.Handler):
    """
    Output log records through a :py:class`betty.user.User`.
    """

    _original_log_level: int

    def __init__(self, user: User, /):
        super().__init__()
        self._user = user
        self._result = Result(self._consume)
        self._thread = threading.Thread(
            name=self.__class__.__name__, target=suppress(self._result, BaseException)
        )
        self._queue = Queue[Callable[[], Coroutine[None, None, None]]]()
        self._finish = threading.Event()
        self._loop = get_running_loop()
        self._logger = logging.root

    @override
    async def bootstrap(self) -> None:
        self._original_log_level = self._logger.level
        self._logger.setLevel(severity_to_log_level[self._user.severity])
        self._logger.addHandler(self)
        self._thread.start()

    @override
    async def shutdown(self, *, wait: bool = True) -> None:
        self._finish.set()
        self._logger.setLevel(self._original_log_level)
        self._logger.removeHandler(self)
        with contextlib.suppress(CancelledError):
            await to_thread(self._thread.join)
        # If no log messages were recorded, there is no result.
        with contextlib.suppress(ResultUnavailable):
            self._result.result()

    def _consume(self) -> None:
        final_iteration = False
        while True:
            try:
                task = self._queue.get_nowait()
            except Empty:
                if self._finish.is_set():
                    # Perform one final iteration to account for race conditions between the finish event being set and
                    # the final tasks being added to the queue.
                    if final_iteration:
                        return
                    final_iteration = True
                # Sleep to prevent the loop from taking up CPU time when the queue is empty.
                sleep(0.001)
            else:
                run_coroutine_threadsafe(task(), self._loop).result()

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self._queue.put_nowait(partial(self._user.log, record))
