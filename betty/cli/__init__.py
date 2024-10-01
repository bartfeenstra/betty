"""
Provide the Command Line Interface.
"""

from __future__ import annotations

import logging
from asyncio import run
from dataclasses import dataclass
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
from typing import final, IO, Any, TYPE_CHECKING

import click
from typing_extensions import override, ClassVar

from betty import about
from betty.app import App
from betty.cli.commands import BettyCommand, Command

if TYPE_CHECKING:
    from betty.locale.localizer import Localizer
    from betty.machine_name import MachineName
    from collections.abc import Iterable, Mapping


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


class _BettyCommands(BettyCommand, click.MultiCommand):
    terminal_width: ClassVar[int | None] = None
    _bootstrapped = False
    _app: ClassVar[App]
    _localizer: ClassVar[Localizer]
    _commands: ClassVar[Mapping[MachineName, type[Command]]]

    @classmethod
    async def new_type_for_app(cls, app: App) -> type[_BettyCommands]:
        from betty.cli import commands

        return await cls._new_type(
            app,
            await app.localizer,
            {
                command.plugin_id(): command
                async for command in commands.COMMAND_REPOSITORY
            },
        )

    @classmethod
    async def _new_type(
        cls,
        app: App,
        localizer: Localizer,
        commands: Mapping[MachineName, type[Command]],
    ) -> type[_BettyCommands]:
        class __BettyCommands(_BettyCommands):
            _app = app
            _localizer = localizer
            _commands = commands

        return __BettyCommands

    def _bootstrap(self) -> None:
        if not self._bootstrapped:
            logging.getLogger().addHandler(_ClickHandler())
            self._bootstrapped = True

    @override
    def list_commands(self, ctx: click.Context) -> Iterable[str]:
        self._bootstrap()
        return list(self._commands)

    @override
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        self._bootstrap()
        try:
            return self._commands[cmd_name].click_command()
        except KeyError:
            return None

    @override
    def make_context(
        self,
        info_name: str,
        args: list[str],
        parent: click.Context | None = None,
        **extra: Any,
    ) -> click.Context:
        if self.terminal_width is not None:
            extra["terminal_width"] = self.terminal_width
        ctx = super().make_context(info_name, args, parent, **extra)
        ctx.obj = _ContextAppObject(self._app, self._localizer)
        return ctx


@dataclass
class _ContextAppObject:
    app: App
    localizer: Localizer


def ctx_app_object(ctx: click.Context) -> _ContextAppObject:
    """
    Get the running application object from a context.

    :param ctx: The context to get the application from. Defaults to the current context.
    """
    app = ctx.find_object(_ContextAppObject)
    assert isinstance(app, _ContextAppObject)
    return app


def main(*args: str) -> Any:
    """
    Launch Betty's Command-Line Interface.

    This is a stand-alone entry point that will manage an event loop and Betty application.
    """
    return run(_main(*args))


async def _main(*args: str) -> Any:
    async with App.new_from_environment() as app, app:
        main_command = await new_main_command(app)
        return main_command(*args)


async def new_main_command(app: App) -> click.Command:
    """
    Create a new Click command for the Betty Command Line Interface.
    """

    @click.command(
        "betty",
        cls=await _BettyCommands.new_type_for_app(app),
        # Set an empty help text so Click does not automatically use the function's docstring.
        help="",
    )
    @click.version_option(
        about.version_label(),
        message=await about.report(),
        prog_name="Betty",
    )
    def main_command(*args: str) -> None:
        pass  # pragma: no cover

    return main_command
