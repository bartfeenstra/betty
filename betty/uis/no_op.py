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

    from betty.localizable import ResolvableLocalizable
    from betty.progress import Progress
    from betty.user import Severity
    from betty.user.error import UserFacingError
    from betty.validation import Validator


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
    async def error(
        self, error: UserFacingError, message: ResolvableLocalizable = "{error}", /
    ) -> None:
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
    ) -> AsyncGenerator[Progress]:
        yield NoOpProgress()

    @override
    async def ask_confirmation(
        self, statement: ResolvableLocalizable, /, *, default: bool = False
    ) -> bool:
        raise UiTimeoutError

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
        validator: Validator[str, T],
        default: str | NoDefault = NoDefault,
    ) -> T:
        pass

    @override
    async def ask_input(self, question, /, *, validator=None, default=NoDefault):
        raise UiTimeoutError
