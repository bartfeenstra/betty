"""
User sessions that do nothing.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TypeVar, final, overload

from typing_extensions import override

from betty.assertion import Assertion
from betty.locale.localizable import Localizable
from betty.progress import Progress
from betty.progress.no_op import NoOpProgress
from betty.typing import Void
from betty.user import User, UserTimeoutError, Verbosity

_T = TypeVar("_T")


@final
class NoOpUser(User):
    """
    A user session that does nothing.
    """

    verbosity = Verbosity.DEFAULT

    @override
    async def set_verbosity(self, verbosity: Verbosity) -> None:
        self.verbosity = verbosity

    @override
    async def message_exception(self) -> None:
        pass

    @override
    async def message_error(self, message: Localizable) -> None:
        pass

    @override
    async def message_warning(self, message: Localizable) -> None:
        pass

    @override
    async def message_information(self, message: Localizable) -> None:
        pass

    @override
    async def message_information_details(self, message: Localizable) -> None:
        pass

    @override
    async def message_debug(self, message: Localizable) -> None:
        pass

    @override
    async def message_log(self, message: logging.LogRecord) -> None:
        pass

    @override
    @asynccontextmanager
    async def message_progress(self, message: Localizable) -> AsyncIterator[Progress]:
        yield NoOpProgress()

    @override
    async def ask_confirmation(
        self, statement: Localizable, *, default: bool = False
    ) -> bool:
        raise UserTimeoutError

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

    @override
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T] | None = None,
        default: str | _T | Void = Void(),  # noqa B008
    ) -> str | _T:
        raise UserTimeoutError
