"""
Console user sessions.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TextIO, cast, final, overload, override

from rich.console import Console
from rich.progress import BarColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.progress import Progress as _RichProgress
from rich.prompt import Confirm, Prompt

from betty.assertion import Assertion
from betty.life_cycle.manage import ManagedLifeCycle
from betty.locale.localizable import ResolvableLocalizable
from betty.locale.localize import resolve_localized
from betty.progress import Progress
from betty.progress.no_op import NoOpProgress
from betty.rich import Theme
from betty.rich.progress import RichProgress
from betty.typing import Void, internal
from betty.user import User, Verbosity
from betty.user.logging import UserHandler


@internal
@final
class RichUser(ManagedLifeCycle, User):
    """
    A Rich user session.
    """

    def __init__(self):
        super().__init__()
        self.life_cycle.on_bootstrap(self._propagate_verbosity)
        self.life_cycle.on_shutdown(self._shutdown_logging_handler)
        self._console = Console(theme=Theme())
        self._verbosity = Verbosity.DEFAULT
        self._logging_handler: UserHandler | None = None
        self._logger = logging.getLogger()
        self._log_formatter = logging.Formatter()

    @property
    def console(self) -> Console:
        """
        The Rich console.
        """
        return self._console

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
        self._console.print_exception(show_locals=self.verbosity >= Verbosity.VERBOSE)

    @override
    async def message_error(self, message: ResolvableLocalizable, /) -> None:
        self._message_error(resolve_localized(message, localizer=self.localizer))

    def _message_error(self, message: str) -> None:
        self.assert_alive()
        self._console.print(f"[red]{message}[/]")

    @override
    async def message_warning(self, message: ResolvableLocalizable, /) -> None:
        self.assert_alive()
        if self._verbosity < Verbosity.DEFAULT:
            return
        self._console.print(
            f"[yellow]{resolve_localized(message, localizer=self.localizer)}[/]"
        )

    @override
    async def message_information(self, message: ResolvableLocalizable, /) -> None:
        self.assert_alive()
        if self._verbosity < Verbosity.DEFAULT:
            return
        self._console.print(
            f"[green]{resolve_localized(message, localizer=self.localizer)}[/]"
        )

    @override
    async def message_information_details(
        self, message: ResolvableLocalizable, /
    ) -> None:
        self.assert_alive()
        if self._verbosity < Verbosity.VERBOSE:
            return
        self._console.print(
            f"[green]{resolve_localized(message, localizer=self.localizer)}[/]"
        )

    @override
    async def message_debug(self, message: ResolvableLocalizable, /) -> None:
        self.assert_alive()
        if self._verbosity < Verbosity.MORE_VERBOSE:
            return
        self._console.print(
            f"[white]{resolve_localized(message, localizer=self.localizer)}[/]"
        )

    @override
    async def message_log(self, message: logging.LogRecord, /) -> None:
        self.assert_bootstrapped()
        if self._verbosity < Verbosity.MOST_VERBOSE:
            return
        self._console.print(f"[blue]{self._log_formatter.format(message)}[/]")

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
                console=self._console,
            ) as rich_progress:
                yield RichProgress(
                    rich_progress, resolve_localized(message, localizer=self.localizer)
                )

    @override
    async def ask_confirmation(
        self,
        statement: ResolvableLocalizable,
        *,
        default: bool = False,
        stdin: TextIO | None = None,
    ) -> bool:
        self.assert_alive()
        return Confirm.ask(
            resolve_localized(statement, localizer=self.localizer),
            console=self._console,
            default=default,
            stream=stdin,
        )

    @overload
    async def ask_input(
        self,
        question: ResolvableLocalizable,
        *,
        default: str | Void = Void(),  # noqa: B008
        stdin: TextIO | None = None,
    ) -> str:
        pass

    @overload
    async def ask_input[T](
        self,
        question: ResolvableLocalizable,
        *,
        assertion: Assertion[str, T],
        default: str | Void = Void(),  # noqa: B008
        stdin: TextIO | None = None,
    ) -> T:
        pass

    @override
    async def ask_input[T](
        self,
        question: ResolvableLocalizable,
        *,
        assertion: Assertion[str, T] | None = None,
        default: str | Void = Void(),  # noqa: B008
        stdin: TextIO | None = None,
    ) -> str | T:
        self.assert_alive()
        ask_kwargs = {}
        if not isinstance(default, Void):
            ask_kwargs["default"] = default
        value = cast(
            str,
            Prompt.ask(
                resolve_localized(question, localizer=self.localizer),
                console=self._console,
                stream=stdin,
                **ask_kwargs,
            ),
        )
        if assertion is None:
            return value
        return assertion(value)
