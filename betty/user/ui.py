"""
User interfaces.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Final, final, overload

from babel import Locale
from babel import default_locale as babel_default_locale
from typing_extensions import sentinel

from betty.locale import default_locale
from betty.user import Severity
from betty.user.logging import log_level_to_severity

if TYPE_CHECKING:
    import logging
    from contextlib import AbstractAsyncContextManager

    from betty.functools import Pipe
    from betty.localizable import ResolvableLocalizable
    from betty.localizer import Localizer
    from betty.progress import Progress
    from betty.user.error import UserFacingError

NoDefault = sentinel("NoDefault")


class Ui(metaclass=ABCMeta):
    """
    A user interface.
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
    async def error(
        self, error: UserFacingError, message: ResolvableLocalizable = "{error}", /
    ) -> None:
        """
        Send a message about a user-facing error to the user.

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

        :raises: betty.user.ui.UiTimeoutError
        """

    @overload
    async def ask_input(
        self,
        question: ResolvableLocalizable,
        /,
        *,
        validator: None = None,
        default: str | NoDefault = NoDefault,
    ) -> str:
        pass

    @overload
    async def ask_input[T](
        self,
        question: ResolvableLocalizable,
        /,
        *,
        validator: Pipe[str, T],
        default: str | NoDefault = NoDefault,
    ) -> T:
        pass

    @abstractmethod
    async def ask_input(self, question, /, *, validator=None, default=NoDefault):
        """
        Ask the user to input text.

        :raises: betty.user.ui.UiTimeoutError
        """


class UiError(Exception):
    """
    A user interface error.
    """


class UiTimeoutError(UiError):
    """
    The user did not respond within the given time, or at all.
    """
