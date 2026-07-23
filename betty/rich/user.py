"""
Console user sessions.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Final, TextIO, cast, final, overload, override

from rich.console import Console
from rich.markup import escape
from rich.progress import BarColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.progress import Progress as _RichProgress
from rich.prompt import Confirm, Prompt

from betty.localizer import default_localizer
from betty.nothing import Nothing, NothingType
from betty.progresses.no_op import NoOpProgress
from betty.progresses.rich import RichProgress
from betty.rich import Theme
from betty.user import Severity, User

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Mapping

    from betty.functools import Pipe
    from betty.localizable import ResolvableLocalizable
    from betty.localizer import Localizer
    from betty.progress import Progress


@final
class RichUser(User):
    """
    A Rich user session.
    """

    _severity_to_style: Final[Mapping[Severity, str]] = {
        Severity.ERROR: "red",
        Severity.WARN: "yellow",
        Severity.CONFIRM: "green",
        Severity.INFO: "white",
        Severity.DEBUG: "white",
    }

    def __init__(
        self,
        *,
        localizer: Localizer = default_localizer,
        severity: Severity | bool = User.default_severity,
    ):
        super().__init__()
        self.console: Final[Console] = Console(theme=Theme())
        """
        The Rich console.
        """
        self._log_formatter = logging.Formatter()
        self._localizer = localizer
        self.severity = severity

    def _print(self, message: ResolvableLocalizable, style: str, /) -> None:
        self.console.print(
            self.localizer.localize(message), emoji=False, markup=False, style=style
        )

    @override
    @property
    def localizer(self) -> Localizer:
        return self._localizer

    @override
    async def exception(self) -> None:
        self.console.print_exception(show_locals=self.shows(Severity.DEBUG))

    @override
    async def message(
        self, message: ResolvableLocalizable, severity: Severity, /
    ) -> None:
        if self.shows(severity):
            self._print(
                self.localizer.localize(message), self._severity_to_style[severity]
            )

    @override
    async def log(self, record: logging.LogRecord, /) -> None:
        if severity := self.logs(record.levelno):
            self.console.print(
                f"[blue]LOG:[/] [{self._severity_to_style[severity]}]{escape(self._log_formatter.format(record))}[/]",
                emoji=False,
            )

    @override
    @asynccontextmanager
    async def progress(
        self, message: ResolvableLocalizable, /
    ) -> AsyncIterator[Progress]:
        if self.shows(Severity.CONFIRM):
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
        else:
            yield NoOpProgress()

    @override
    async def ask_confirmation(
        self,
        statement: ResolvableLocalizable,
        /,
        *,
        default: bool = False,
        stdin: TextIO | None = None,
    ) -> bool:
        return Confirm.ask(
            escape(self.localizer.localize(statement)),
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
        ask_kwargs = {}
        if default is not Nothing:
            ask_kwargs["default"] = default
        value = cast(
            str,
            Prompt.ask(
                escape(self.localizer.localize(question)),
                console=self.console,
                stream=stdin,
                **ask_kwargs,
            ),
        )
        if assertion is None:
            return value
        return assertion(value)
