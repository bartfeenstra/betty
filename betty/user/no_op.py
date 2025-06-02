"""
User sessions that do nothing.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import final, overload

from typing_extensions import override

from betty.assertion import Assertion
from betty.locale.localizable import Localizable
from betty.progress import Progress
from betty.progress.no_op import NoOpProgress
from betty.test_utils.console import _T
from betty.typing import Void
from betty.user import User, UserTimeoutError


@final
class NoOpUser(User):
    """
    A user session that does nothing.
    """

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
    async def message_debug(self, message: Localizable) -> None:
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
        default: str | type[Void] = Void,
    ) -> str:
        pass

    @overload
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T],
        default: str | type[Void] = Void,
    ) -> _T:
        pass

    @override
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T] | None = None,
        default: str | _T | type[Void] = Void,
    ) -> str | _T:
        raise UserTimeoutError
