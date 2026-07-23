"""
User sessions that do nothing.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Final, final, overload, override

from betty.localizer import Localizer, default_localizer
from betty.nothing import Nothing, NothingType
from betty.progresses.no_op import NoOpProgress
from betty.user import Severity, User, UserTimeoutError

if TYPE_CHECKING:
    import logging
    from collections.abc import AsyncIterator

    from betty.functools import Pipe
    from betty.localizable import ResolvableLocalizable
    from betty.progress import Progress


@final
class NoOpUser(User):
    """
    A user session that does nothing.
    """

    localizer: Final[Localizer] = default_localizer

    @override
    async def exception(self) -> None:
        pass

    @override
    async def message(
        self, message: ResolvableLocalizable, severity: Severity, /
    ) -> None:
        pass

    @override
    async def log(self, record: logging.LogRecord, /) -> None:
        pass

    @override
    @asynccontextmanager
    async def progress(
        self, message: ResolvableLocalizable, /
    ) -> AsyncIterator[Progress]:
        yield NoOpProgress()

    @override
    async def ask_confirmation(
        self, statement: ResolvableLocalizable, /, *, default: bool = False
    ) -> bool:
        raise UserTimeoutError

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

    @override
    async def ask_input(self, question, /, *, assertion=None, default=Nothing):
        raise UserTimeoutError
