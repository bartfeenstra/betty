"""
Console user sessions.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Final, TextIO, cast, final, overload, override

from rich.console import Console
from rich.progress import BarColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.progress import Progress as _RichProgress
from rich.prompt import Confirm, Prompt

from betty.life_cycle.manage import ManagedLifeCycle
from betty.nothing import Nothing, NothingType
from betty.progresses.no_op import NoOpProgress
from betty.progresses.rich import RichProgress
from betty.rich import Theme
from betty.user import User, Verbosity
from betty.user.logging import UserHandler

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from betty.functools import Pipe
    from betty.localizable import ResolvableLocalizable
    from betty.progress import Progress


@final
class RichUser(ManagedLifeCycle, User):
    """
    A Rich user session.
    """

    def __init__(self):
        super().__init__()
        self.life_cycle.on_bootstrap(self._propagate_verbosity)
        self.life_cycle.on_shutdown(self._shutdown_logging_handler)
        self.console: Final[Console] = Console(theme=Theme())
        """
        The Rich console.
        """
        self._verbosity = Verbosity.DEFAULT
        self._logging_handler: UserHandler | None = None
        self._logger = logging.getLogger()
        self._log_formatter = logging.Formatter()

    @override
    @property
    def verbosity(self) -> Verbosity:
        return self._verbosity

    @override
    async def set_verbosity(self, verbosity: Verbosity, /) -> None:
        if verbosity is self._verbosity:
            return
        self._verbosity = verbosity
        if self.bootstrapped:
            await self._propagate_verbosity()

    async def _shutdown_logging_handler(self, *, wait: bool = True) -> None:
        if self._logging_handler is not None:
            await self._logging_handler.shutdown(wait=wait)

    async def _propagate_verbosity(self) -> None:
        if self.verbosity >= Verbosity.MOST_VERBOSE:
            if self._logging_handler is not None:
                return

            self._logging_handler = UserHandler(self)
            self._logger.addHandler(self._logging_handler)
            await self._logging_handler.bootstrap()
            level = logging.NOTSET
        else:
            if self._logging_handler is None:
                return
            self._logger.removeHandler(self._logging_handler)
            await self._logging_handler.shutdown()
            level = 999999999
        self._logger.setLevel(level)

    @override
    async def message_exception(self) -> None:
        self._message_error(self.localizer._("An unexpected error occurred:"))
        self.console.print_exception(show_locals=self.verbosity >= Verbosity.VERBOSE)

    @override
    async def message_error(self, message: ResolvableLocalizable, /) -> None:
        self._message_error(self.localizer.localize(message))

    def _message_error(self, message: str) -> None:
        self.assert_alive()
        self.console.print(f"[red]{message}[/]")

    @override
    async def message_warning(self, message: ResolvableLocalizable, /) -> None:
        self.assert_alive()
        if self._verbosity < Verbosity.DEFAULT:
            return
        self.console.print(f"[yellow]{self.localizer.localize(message)}[/]")

    @override
    async def message_information(self, message: ResolvableLocalizable, /) -> None:
        self.assert_alive()
        if self._verbosity < Verbosity.DEFAULT:
            return
        self.console.print(f"[green]{self.localizer.localize(message)}[/]")

    @override
    async def message_information_details(
        self, message: ResolvableLocalizable, /
    ) -> None:
        self.assert_alive()
        if self._verbosity < Verbosity.VERBOSE:
            return
        self.console.print(f"[green]{self.localizer.localize(message)}[/]")

    @override
    async def message_debug(self, message: ResolvableLocalizable, /) -> None:
        self.assert_alive()
        if self._verbosity < Verbosity.MORE_VERBOSE:
            return
        self.console.print(f"[white]{self.localizer.localize(message)}[/]")

    @override
    async def message_log(self, message: logging.LogRecord, /) -> None:
        self.assert_bootstrapped()
        if self._verbosity < Verbosity.MOST_VERBOSE:
            return
        self.console.print(f"[blue]{self._log_formatter.format(message)}[/]")

    @override
    @asynccontextmanager
    async def message_progress(
        self, message: ResolvableLocalizable, /
    ) -> AsyncIterator[Progress]:
        self.assert_alive()
        if self.verbosity < Verbosity.DEFAULT:
            yield NoOpProgress()
        else:
            with _RichProgress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self.console,
            ) as rich_progress:
                async with RichProgress(
                    rich_progress, self.localizer.localize(message)
                ) as progress:
                    yield progress

    @override
    async def ask_confirmation(
        self,
        statement: ResolvableLocalizable,
        /,
        *,
        default: bool = False,
        stdin: TextIO | None = None,
    ) -> bool:
        self.assert_alive()
        return Confirm.ask(
            self.localizer.localize(statement),
            console=self.console,
            default=default,
            stream=stdin,
        )

    @overload
    async def ask_input(
        self,
        question: ResolvableLocalizable,
        /,
        *,
        assertion: None = None,
        default: str | NothingType = Nothing,
        stdin: TextIO | None = None,
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
        stdin: TextIO | None = None,
    ) -> T:
        pass

    @override
    async def ask_input(
        self,
        question,
        /,
        *,
        assertion=None,
        default=Nothing,
        stdin: TextIO | None = None,
    ):
        self.assert_alive()
        ask_kwargs = {}
        if default is not Nothing:
            ask_kwargs["default"] = default
        value = cast(
            str,
            Prompt.ask(
                self.localizer.localize(question),
                console=self.console,
                stream=stdin,
                **ask_kwargs,
            ),
        )
        if assertion is None:
            return value
        return assertion(value)
