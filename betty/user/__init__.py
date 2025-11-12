"""
An API to interact with Betty's user.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TYPE_CHECKING, Self, TypeVar, final, overload

from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.typing import Void

if TYPE_CHECKING:
    import logging
    from contextlib import AbstractAsyncContextManager
    from types import TracebackType

    from betty.assertion import Assertion
    from betty.locale.localizable import Localizable
    from betty.locale.localizer import Localizer
    from betty.progress import Progress


_T = TypeVar("_T")


class Verbosity(IntEnum):
    """
    User interaction verbosity.
    """

    QUIET = -1
    #: Inform users of errors, but do not show any other output.
    DEFAULT = 0
    #: Like QUIET, and show warning and information summary messages.
    VERBOSE = 1
    #: Like DEFAULT, and show information details messages,
    MORE_VERBOSE = 2
    #: Like VERBOSE, and show debug messages.
    MOST_VERBOSE = 3
    #: Like MORE_VERBOSE, and show all log messages.


class UserError(Exception):
    """
    A user session error.
    """


class UserTimeoutError(UserError):
    """
    The user did not respond within the given time, or at all.
    """


class User(ABC):
    """
    A user session.
    """

    localizer: Localizer = DEFAULT_LOCALIZER

    async def connect(self) -> None:
        """
        Connect to the current user.
        """
        return

    async def disconnect(self) -> None:
        """
        Disconnect from the current user.
        """
        return

    @final
    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    @final
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.disconnect()

    @property
    @abstractmethod
    def verbosity(self) -> Verbosity:
        """
        The current verbosity.
        """

    @abstractmethod
    async def set_verbosity(self, verbosity: Verbosity) -> None:
        """
        Set the new verbosity.
        """

    @abstractmethod
    async def message_exception(self) -> None:
        """
        Send an error message about an exception to the user.

        An error indicates that something went wrong, and Betty was unable to perform an expected action.

        These messages are always shown to the user.
        """

    @abstractmethod
    async def message_error(self, message: Localizable) -> None:
        """
        Send an error message to the user.

        An error indicates that something went wrong, and Betty was unable to perform an expected action.

        These messages are always shown to the user.
        """

    @abstractmethod
    async def message_warning(self, message: Localizable) -> None:
        """
        Send a warning message to the user.

        A warning indicates that something went wrong, but that Betty was able to recover and perform an expected
        action, but perhaps in a slightly different way.

        These messages are shown to users for :py:attr:`betty.user.Verbosity.DEFAULT` and up.
        """

    @abstractmethod
    async def message_information(self, message: Localizable) -> None:
        """
        Send a summarized informative message to the user.

        An informative message tells the user that something happened successfully, e.g. the starting or finishing of a
        task.

        These messages are shown to users for :py:attr:`betty.user.Verbosity.DEFAULT` and up.
        """

    @abstractmethod
    async def message_information_details(self, message: Localizable) -> None:
        """
        Send a detailed informative message to the user.

        An informative message tells the user that something happened successfully, e.g. the starting or finishing of a
        task.

        These messages are shown to users for :py:attr:`betty.user.Verbosity.VERBOSE` and up.
        """

    @abstractmethod
    async def message_debug(self, message: Localizable) -> None:
        """
        Send a debugging message to the user.

        These messages are shown to users for :py:attr:`betty.user.Verbosity.MORE_VERBOSE` and up.
        """

    @abstractmethod
    async def message_log(self, message: logging.LogRecord) -> None:
        """
        Send a log message to the user.

        These messages are shown to users for :py:attr:`betty.user.Verbosity.MOST_VERBOSE` and up.
        """

    @abstractmethod
    def message_progress(
        self, message: Localizable
    ) -> AbstractAsyncContextManager[Progress]:
        """
        Send information about a progressing activity to the user.

        These messages are shown to users for :py:attr:`betty.user.Verbosity.DEFAULT` and up.
        """

    @abstractmethod
    async def ask_confirmation(
        self, statement: Localizable, *, default: bool = False
    ) -> bool:
        """
        Ask the user to confirm a statement.

        :raises: betty.user.UserTimeoutError
        """

    @overload
    async def ask_input(
        self,
        question: Localizable,
        *,
        default: str | Void = Void(),  # noqa B008
    ) -> str:
        pass

    @overload
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T],
        default: str | Void = Void(),  # noqa B008
    ) -> _T:
        pass

    @abstractmethod
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T] | None = None,
        default: str | _T | Void = Void(),  # noqa B008
    ) -> str | _T:
        """
        Ask the user to input text.

        :raises: betty.user.UserTimeoutError
        """
