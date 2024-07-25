"""
Provide the Command Line Interface.
"""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from logging import (
    Handler,
    CRITICAL,
    ERROR,
    WARNING,
    INFO,
    DEBUG,
    NOTSET,
    LogRecord,
)
from sys import stderr
from typing import Iterator, TYPE_CHECKING, final, IO, Any, TypeVar

import click
from click import Context
from typing_extensions import override, ClassVar

from betty import about
from betty.asyncio import wait_to_thread
from betty.error import UserFacingError
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.plugin import PluginRepository, PluginNotFound

if TYPE_CHECKING:
    from betty.assertion import Assertion
    from betty.cli.commands import Command


@contextmanager
def catch_exceptions() -> Iterator[None]:
    """
    Catch and log all exceptions.
    """
    try:
        yield
    except KeyboardInterrupt:
        print("Quitting...")  # noqa T201
        sys.exit(0)
    except Exception as e:
        logger = logging.getLogger(__name__)
        if isinstance(e, UserFacingError):
            logger.error(e.localize(DEFAULT_LOCALIZER))
        else:
            logger.exception(e)
        sys.exit(1)


_ValueT = TypeVar("_ValueT")
_ReturnT = TypeVar("_ReturnT")


def assertion_to_value_proc(
    assertion: Assertion[_ValueT, _ReturnT], localizer: Localizer
) -> Assertion[_ValueT, _ReturnT]:
    """
    Convert an :py:class:`betty.assertion.Assertion` to a Click ``value_proc`` callback.
    """

    def _assert(value: _ValueT) -> _ReturnT:
        try:
            return assertion(value)
        except UserFacingError as error:
            raise click.BadParameter(error.localize(localizer)) from None

    return _assert


@final
class _ClickHandler(Handler):
    """
    Output log records to stderr with :py:func:`click.secho`.
    """

    COLOR_LEVELS = {
        CRITICAL: "red",
        ERROR: "red",
        WARNING: "yellow",
        INFO: "green",
        DEBUG: "white",
        NOTSET: "white",
    }

    def __init__(self, stream: IO[Any] = stderr):
        super().__init__(-1)
        self._stream = stream

    @override
    def emit(self, record: LogRecord) -> None:
        click.secho(self.format(record), file=self._stream, fg=self._color(record))

    def _color(self, record: LogRecord) -> str:
        for level, color in self.COLOR_LEVELS.items():
            if record.levelno >= level:
                return color
        return self.COLOR_LEVELS[NOTSET]


class _BettyCommands(click.MultiCommand):
    terminal_width: ClassVar[int | None] = None
    _bootstrapped = False
    commands: PluginRepository[Command]

    def _bootstrap(self) -> None:
        if not self._bootstrapped:
            logging.getLogger().addHandler(_ClickHandler())
            self._bootstrapped = True

    @override
    @catch_exceptions()
    def list_commands(self, ctx: click.Context) -> list[str]:
        from betty.cli import commands

        self._bootstrap()
        return [
            command.plugin_id()
            for command in wait_to_thread(commands.COMMAND_REPOSITORY.select())
        ]

    @override
    @catch_exceptions()
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        from betty.cli import commands

        self._bootstrap()
        try:
            return wait_to_thread(
                commands.COMMAND_REPOSITORY.get(cmd_name)
            ).click_command()
        except PluginNotFound:
            return None

    @override
    def make_context(
        self,
        info_name: str | None,
        args: list[str],
        parent: Context | None = None,
        **extra: Any,
    ) -> Context:
        if self.terminal_width is not None:
            extra["terminal_width"] = self.terminal_width
        return super().make_context(
            info_name,  # type: ignore[arg-type]
            args,
            parent,
            **extra,
        )


@click.command(
    "betty",
    cls=_BettyCommands,
    # Set an empty help text so Click does not automatically use the function's docstring.
    help="",
)
@click.version_option(
    wait_to_thread(about.version_label()),
    message=wait_to_thread(about.report()),
    prog_name="Betty",
)
def main() -> None:
    """
    Launch Betty's Command-Line Interface.
    """
    pass  # pragma: no cover
