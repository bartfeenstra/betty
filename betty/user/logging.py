"""
Integrate the user API with Python's :py:mod:`logging`.
"""

from __future__ import annotations

import contextlib
import logging
import threading
from _asyncio import get_running_loop
from _queue import Empty
from asyncio import CancelledError, run_coroutine_threadsafe, to_thread
from collections.abc import Callable, Coroutine, Mapping
from functools import partial
from queue import Queue
from time import sleep
from typing import TYPE_CHECKING, Final, final, override

from betty.functools import Result, ResultUnavailable, suppress
from betty.life_cycle import LifeCycle
from betty.user import Severity

if TYPE_CHECKING:
    from betty.user.ui import Ui


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


@final
class UiHandler(LifeCycle, logging.Handler):
    """
    Output log records through a :py:class`betty.user.ui.Ui`.
    """

    _original_log_level: int

    def __init__(self, ui: Ui, /):
        super().__init__()
        self._ui = ui
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
        self._logger.setLevel(severity_to_log_level[self._ui.severity])
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
        self._queue.put_nowait(partial(self._ui.log, record))
