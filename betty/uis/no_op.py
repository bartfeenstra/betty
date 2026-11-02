"""
User interfaces that do nothing.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Final, final, overload, override

from betty.localizer import Localizer, default_localizer
from betty.progresses.no_op import NoOpProgress
from betty.user.ui import NoDefault, Ui, UiTimeoutError

if TYPE_CHECKING:
    import logging
    from collections.abc import AsyncGenerator

    from betty.localizer import AnyLocalizable
    from betty.pipeline import Pipe
    from betty.progress import Progress
    from betty.user import Severity


@final
class NoOpUi(Ui):
    """
    A user interface that does nothing.
    """

    localizer: Final[Localizer] = default_localizer

    @override
    async def exception(self) -> None:
        pass

    @override
    async def message(self, message: AnyLocalizable, severity: Severity, /) -> None:
        pass

    @override
    async def log(self, record: logging.LogRecord, /) -> None:
        pass

    @override
    @asynccontextmanager
    async def progress(self, message: AnyLocalizable, /) -> AsyncGenerator[Progress]:
        yield NoOpProgress()

    @override
    async def ask_confirmation(
        self, statement: AnyLocalizable, /, *, default: bool = False
    ) -> bool:
        raise UiTimeoutError

    @overload
    async def ask_input(
        self,
        question: AnyLocalizable,
        /,
        *,
        assertion: None = None,
        default: str | NoDefault = NoDefault,
    ) -> str:
        pass

    @overload
    async def ask_input[T](
        self,
        question: AnyLocalizable,
        /,
        *,
        assertion: Pipe[str, T],
        default: str | NoDefault = NoDefault,
    ) -> T:
        pass

    @override
    async def ask_input(self, question, /, *, assertion=None, default=NoDefault):
        raise UiTimeoutError
