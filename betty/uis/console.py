"""
Console user interfaces.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    TextIO,
    cast,
    final,
    overload,
    override,
)

from rich.console import Console as RichConsole
from rich.markdown import Markdown
from rich.markup import escape
from rich.progress import BarColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.progress import Progress as _RichProgress
from rich.prompt import Confirm, Prompt

from betty.localizable import Localizable
from betty.localizables.gettext import _
from betty.localizer import default_localizer
from betty.progresses.no_op import NoOpProgress
from betty.progresses.rich import RichProgress
from betty.rich import Theme
from betty.user import Severity
from betty.user.ui import NoDefault, Ui

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Mapping, MutableSequence

    from betty.localizable import ResolvableLocalizable
    from betty.localizer import Localizer
    from betty.progress import Progress
    from betty.user.error import UserFacingError
    from betty.validation import Validator


@final
class Console(Ui):
    """
    Betty's console user interface.
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
        severity: Severity | bool = Ui.default_severity,
    ):
        super().__init__()
        self.console: Final[RichConsole] = RichConsole(theme=Theme())
        """
        The Rich console.
        """
        self._log_formatter = logging.Formatter()
        self._localizer = localizer
        self.severity = severity

    def _print(self, *messages: Any, style: str) -> None:
        self.console.print(
            *(
                self.localizer.localize(message)
                if isinstance(message, Localizable)
                else message
                for message in messages
            ),
            emoji=False,
            markup=False,
            style=style,
        )

    @override
    @property
    def localizer(self) -> Localizer:
        return self._localizer

    @override
    async def exception(self) -> None:
        self.console.print_exception(show_locals=self.shows(Severity.DEBUG))

    @override
    async def error(
        self, error: UserFacingError, message: ResolvableLocalizable = "{error}", /
    ) -> None:
        # @todo Add test coverage
        # @todo
        # @todo
        # @todo Extract single Invalid formatting into a separate function.
        # @todo Then, here, support formatting InvalidGroup as well.
        # @todo
        # @todo
        messages: MutableSequence[Any] = [
            self.localizer.localize(message).format(
                error=self.localizer.localize(error)
            )
        ]
        if error.location:
            messages.append(Markdown("# " + self.localizer.localize(_("Where"))))
            # @todo
            messages.append("???????")
        if error.hint:
            messages.append(Markdown("# " + self.localizer.localize(_("Why"))))
            messages.append(error.hint)
        if error.url:
            messages.append(Markdown("# " + self.localizer.localize(_("Learn more"))))
            messages.append(
                f"[link={error.url}]{self.localizer.localize(_('Read more'))}[/link]"
            )
        self._print(
            *messages,
            style=self._severity_to_style[Severity.ERROR],
        )

    @override
    async def message(
        self, message: ResolvableLocalizable, severity: Severity, /
    ) -> None:
        if self.shows(severity):
            self._print(
                self.localizer.localize(message),
                style=self._severity_to_style[severity],
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
    ) -> AsyncGenerator[Progress]:
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
        validator: None = None,
        default: str | NoDefault = NoDefault,
        stdin: TextIO | None = None,
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
        stdin: TextIO | None = None,
    ) -> T:
        pass

    @override
    async def ask_input(
        self,
        question,
        /,
        *,
        validator=None,
        default=NoDefault,
        stdin: TextIO | None = None,
    ):
        ask_kwargs = {}
        if default is not NoDefault:
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
        if validator is None:
            return value
        return validator(value)
