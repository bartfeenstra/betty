"""
User sessions that do nothing.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import final, overload, override

from betty.assertion import Assertion
from betty.locale.localizable import ResolvableLocalizable
from betty.progress import Progress
from betty.progress.no_op import NoOpProgress
from betty.typing import Void, VoidType
from betty.user import User, UserTimeoutError, Verbosity


@final
class NoOpUser(User):
    """
    A user session that does nothing.
    """

    verbosity = Verbosity.DEFAULT

    @override
    async def set_verbosity(self, verbosity: Verbosity, /) -> None:
        self.verbosity = verbosity

    @override
    async def message_exception(self) -> None:
        pass

    @override
    async def message_error(self, message: ResolvableLocalizable, /) -> None:
        pass

    @override
    async def message_warning(self, message: ResolvableLocalizable, /) -> None:
        pass

    @override
    async def message_information(self, message: ResolvableLocalizable, /) -> None:
        pass

    @override
    async def message_information_details(
        self, message: ResolvableLocalizable, /
    ) -> None:
        pass

    @override
    async def message_debug(self, message: ResolvableLocalizable, /) -> None:
        pass

    @override
    async def message_log(self, message: logging.LogRecord, /) -> None:
        pass

    @override
    @asynccontextmanager
    async def message_progress(
        self, message: ResolvableLocalizable, /
    ) -> AsyncIterator[Progress]:
        yield NoOpProgress()

    @override
    async def ask_confirmation(
        self, statement: ResolvableLocalizable, *, default: bool = False
    ) -> bool:
        raise UserTimeoutError

    @overload
    async def ask_input(
        self,
        question: ResolvableLocalizable,
        *,
        default: str | VoidType = Void,
    ) -> str:
        pass

    @overload
    async def ask_input[T](
        self,
        question: ResolvableLocalizable,
        *,
        assertion: Assertion[str, T],
        default: str | VoidType = Void,
    ) -> T:
        pass

    @override
    async def ask_input[T](
        self,
        question: ResolvableLocalizable,
        *,
        assertion: Assertion[str, T] | None = None,
        default: str | T | VoidType = Void,
    ) -> str | T:
        raise UserTimeoutError
