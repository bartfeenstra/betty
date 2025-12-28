"""
Console user sessions.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import TextIO, TypeVar, cast, final, overload

from rich.console import Console
from rich.progress import BarColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.progress import Progress as _RichProgress
from rich.prompt import Confirm, Prompt
from typing_extensions import override

from betty.assertion import Assertion
from betty.locale.localizable import LocalizableLike
from betty.locale.localize.ensure import ensure_localized
from betty.progress import Progress
from betty.progress.no_op import NoOpProgress
from betty.rich import Theme
from betty.rich.progress import RichProgress
from betty.typing import Void, internal
from betty.user import User, Verbosity
from betty.user.logging import UserHandler

_T = TypeVar("_T")


@internal
@final
class RichUser(User):
    """
    A Rich user session.
    """

    def __init__(self):
        self._connected = False
        self._exit_stack = AsyncExitStack()
        self._console = Console(theme=Theme())
        self._verbosity = Verbosity.DEFAULT
        self._logging_handler = UserHandler(self)
        self._exit_stack.push_async_callback(self._logging_handler.stop)
        self._logger = logging.getLogger()
        self._log_formatter = logging.Formatter()

    @property
    def console(self) -> Console:
        """
        The Rich console.
        """
        return self._console

    @override
    async def connect(self) -> None:
        self._connected = True
        await self._propagate_verbosity()

    @override
    async def disconnect(self) -> None:
        assert self._connected
        await self._exit_stack.aclose()
        self._connected = False

    @override
    @property
    def verbosity(self) -> Verbosity:
        return self._verbosity

    @override
    async def set_verbosity(self, verbosity: Verbosity, /) -> None:
        if verbosity is self._verbosity:
            return
        self._verbosity = verbosity
        if self._connected:
            await self._propagate_verbosity()

    async def _propagate_verbosity(self) -> None:
        if self.verbosity >= Verbosity.MOST_VERBOSE:
            self._logger.addHandler(self._logging_handler)
            await self._logging_handler.start()
            level = logging.NOTSET
        else:
            self._logger.removeHandler(self._logging_handler)
            await self._logging_handler.stop()
            level = 999999999
        self._logger.setLevel(level)

    @override
    async def message_exception(self) -> None:
        self._message_error(self.localizer._("An unexpected error occurred:"))
        self._console.print_exception(show_locals=self.verbosity >= Verbosity.VERBOSE)

    @override
    async def message_error(self, message: LocalizableLike, /) -> None:
        self._message_error(ensure_localized(message, localizer=self.localizer))

    def _message_error(self, message: str) -> None:
        assert self._connected
        self._console.print(f"[red]{message}[/]")

    @override
    async def message_warning(self, message: LocalizableLike, /) -> None:
        assert self._connected
        if self._verbosity < Verbosity.DEFAULT:
            return
        self._console.print(
            f"[yellow]{ensure_localized(message, localizer=self.localizer)}[/]"
        )

    @override
    async def message_information(self, message: LocalizableLike, /) -> None:
        assert self._connected
        if self._verbosity < Verbosity.DEFAULT:
            return
        self._console.print(
            f"[green]{ensure_localized(message, localizer=self.localizer)}[/]"
        )

    @override
    async def message_information_details(self, message: LocalizableLike, /) -> None:
        assert self._connected
        if self._verbosity < Verbosity.VERBOSE:
            return
        self._console.print(
            f"[green]{ensure_localized(message, localizer=self.localizer)}[/]"
        )

    @override
    async def message_debug(self, message: LocalizableLike, /) -> None:
        assert self._connected
        if self._verbosity < Verbosity.MORE_VERBOSE:
            return
        self._console.print(
            f"[white]{ensure_localized(message, localizer=self.localizer)}[/]"
        )

    @override
    async def message_log(self, message: logging.LogRecord, /) -> None:
        if self._verbosity < Verbosity.MOST_VERBOSE:
            return
        self._console.print(f"[blue]{self._log_formatter.format(message)}[/]")

    @override
    @asynccontextmanager
    async def message_progress(
        self, message: LocalizableLike, /
    ) -> AsyncIterator[Progress]:
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
                    rich_progress, ensure_localized(message, localizer=self.localizer)
                )

    @override
    async def ask_confirmation(
        self,
        statement: LocalizableLike,
        *,
        default: bool = False,
        stdin: TextIO | None = None,
    ) -> bool:
        assert self._connected
        return Confirm.ask(
            ensure_localized(statement, localizer=self.localizer),
            console=self._console,
            default=default,
            stream=stdin,
        )

    @overload
    async def ask_input(
        self,
        question: LocalizableLike,
        *,
        default: str | Void = Void(),  # noqa B008
        stdin: TextIO | None = None,
    ) -> str:
        pass

    @overload
    async def ask_input(
        self,
        question: LocalizableLike,
        *,
        assertion: Assertion[str, _T],
        default: str | Void = Void(),  # noqa B008
        stdin: TextIO | None = None,
    ) -> _T:
        pass

    @override
    async def ask_input(
        self,
        question: LocalizableLike,
        *,
        assertion: Assertion[str, _T] | None = None,
        default: str | Void = Void(),  # noqa B008
        stdin: TextIO | None = None,
    ) -> str | _T:
        assert self._connected
        ask_kwargs = {}
        if not isinstance(default, Void):
            ask_kwargs["default"] = default
        value = cast(
            str,
            Prompt.ask(  # type: ignore[call-overload]
                ensure_localized(question, localizer=self.localizer),
                console=self._console,
                stream=stdin,
                **ask_kwargs,
            ),
        )
        if assertion is None:
            return value
        return assertion(value)
