"""
Console user sessions.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import TextIO, cast, final, overload

from rich.console import Console
from rich.progress import BarColumn, MofNCompleteColumn, TextColumn, TimeElapsedColumn
from rich.progress import Progress as RichProgress
from rich.prompt import Confirm, Prompt
from typing_extensions import override

from betty.assertion import Assertion
from betty.console import _T
from betty.console.progress import ConsoleProgress
from betty.console.rich import ConsoleTheme
from betty.locale.localizable import Localizable
from betty.progress import Progress
from betty.progress.no_op import NoOpProgress
from betty.typing import Void, internal
from betty.user import User, Verbosity
from betty.user.logging import UserHandler


@internal
@final
class ConsoleUser(User):
    """
    A console user session.
    """

    def __init__(self):
        self._connected = False
        self._exit_stack = AsyncExitStack()
        self._rich_console = Console(theme=ConsoleTheme())
        self._verbosity = Verbosity.MORE_VERBOSE
        self._logging_handler = UserHandler(self)
        self._logger = logging.getLogger()

    @override
    async def connect(self) -> None:
        await self._exit_stack.enter_async_context(self._logging_handler)
        self._logger.addHandler(self._logging_handler)
        self._propagate_verbosity()
        self._connected = True

    @override
    async def disconnect(self) -> None:
        assert self._connected
        self._logger.removeHandler(self._logging_handler)
        await self._exit_stack.aclose()
        self._connected = False

    @override  # type: ignore[explicit-override]
    @property
    def verbosity(self) -> Verbosity:
        return self._verbosity

    @verbosity.setter
    def verbosity(self, verbosity: Verbosity) -> None:
        self._verbosity = verbosity
        self._propagate_verbosity()

    def _propagate_verbosity(self) -> None:
        self._logger.setLevel(
            logging.NOTSET
            if self.verbosity is Verbosity.MORE_VERBOSE
            else logging.CRITICAL
        )

    @override
    async def message_exception(self) -> None:
        self._message_error(self.localizer._("An unexpected error occurred:"))
        self._rich_console.print_exception(
            show_locals=self.verbosity >= Verbosity.VERBOSE
        )

    @override
    async def message_error(self, message: Localizable) -> None:
        self._message_error(message.localize(self.localizer))

    def _message_error(self, message: str) -> None:
        assert self._connected
        self._rich_console.print(f"[red]{message}[/]")

    @override
    async def message_warning(self, message: Localizable) -> None:
        assert self._connected
        if self._verbosity < Verbosity.DEFAULT:
            return
        self._rich_console.print(f"[yellow]{message.localize(self.localizer)}[/]")

    @override
    async def message_information(self, message: Localizable) -> None:
        assert self._connected
        if self._verbosity < Verbosity.DEFAULT:
            return
        self._rich_console.print(f"[green]{message.localize(self.localizer)}[/]")

    @override
    async def message_debug(self, message: Localizable) -> None:
        assert self._connected
        if self._verbosity < Verbosity.VERBOSE:
            return
        self._rich_console.print(f"[white]{message.localize(self.localizer)}[/]")

    @override
    @asynccontextmanager
    async def message_progress(self, message: Localizable) -> AsyncIterator[Progress]:
        if self.verbosity < Verbosity.DEFAULT:
            yield NoOpProgress()
        else:
            with RichProgress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=self._rich_console,
            ) as rich_progress:
                yield ConsoleProgress(rich_progress, message.localize(self.localizer))

    @override
    async def ask_confirmation(
        self,
        statement: Localizable,
        *,
        default: bool = False,
        stdin: TextIO | None = None,
    ) -> bool:
        assert self._connected
        return Confirm.ask(
            statement.localize(self.localizer),
            console=self._rich_console,
            default=default,
            stream=stdin,
        )

    @overload
    async def ask_input(
        self,
        question: Localizable,
        *,
        default: str | type[Void] = Void,
        stdin: TextIO | None = None,
    ) -> str:
        pass

    @overload
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T],
        default: str | type[Void] = Void,
        stdin: TextIO | None = None,
    ) -> _T:
        pass

    @override
    async def ask_input(
        self,
        question: Localizable,
        *,
        assertion: Assertion[str, _T] | None = None,
        default: str | type[Void] = Void,
        stdin: TextIO | None = None,
    ) -> str | _T:
        assert self._connected
        ask_kwargs = {}
        if default is not Void:
            ask_kwargs["default"] = default
        value = cast(
            str,
            Prompt.ask(  # type: ignore[call-overload]
                question.localize(self.localizer),
                console=self._rich_console,
                stream=stdin,
                **ask_kwargs,
            ),
        )
        if assertion is None:
            return value
        return assertion(value)
