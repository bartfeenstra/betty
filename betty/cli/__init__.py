"""
Provide the Command Line Interface.
"""

from __future__ import annotations

import logging
import sys
from asyncio import run
from dataclasses import dataclass
from logging import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    NOTSET,
    WARNING,
    Handler,
    LogRecord,
)
from sys import stderr
from typing import IO, TYPE_CHECKING, Any, ClassVar, final

import asyncclick as click
from typing_extensions import override

from betty import about
from betty.app import App

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.locale.localizer import Localizer
    from betty.machine_name import MachineName


@final
class _ClickHandler(Handler):
    """
    Output log records to stderr with :py:func:`asyncclick.secho`.
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


class _BettyCommands(click.Group):
    terminal_width: ClassVar[int | None] = None
    _bootstrapped = False
    _app: ClassVar[App]
    _localizer: ClassVar[Localizer]
    _commands: ClassVar[Mapping[MachineName, click.Command]]

    @classmethod
    async def new_type_for_app(cls, app: App) -> type[_BettyCommands]:
        from betty.cli import commands

        return await cls._new_type(
            app,
            await app.localizer,
            {
                command.plugin_id(): await (
                    await app.new_target(command)
                ).click_command()
                async for command in commands.COMMAND_REPOSITORY
            },
        )

    @classmethod
    async def _new_type(
        cls,
        app: App,
        localizer: Localizer,
        commands: Mapping[MachineName, click.Command],
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
    def list_commands(self, ctx: click.Context) -> list[str]:
        self._bootstrap()
        return list(self._commands)

    @override
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        self._bootstrap()
        try:
            return self._commands[cmd_name]
        except KeyError:
            return None

    @override
    async def make_context(
        self,
        info_name: str | None,
        args: list[str],
        parent: click.Context | None = None,
        **extra: Any,
    ) -> click.Context:
        if self.terminal_width is not None:
            extra["terminal_width"] = self.terminal_width
        ctx = await super().make_context(info_name, args, parent, **extra)
        ctx.obj = ContextAppObject(self._app, self._localizer)
        return ctx


@final
@dataclass(frozen=True)
class ContextAppObject:
    """
    The running Betty application and it localizer.
    """

    app: App
    localizer: Localizer


def ctx_app_object(ctx: click.Context) -> ContextAppObject:
    """
    Get the running application object from a context.

    :param ctx: The context to get the application from. Defaults to the current context.
    """
    app = ctx.find_object(ContextAppObject)
    assert isinstance(app, ContextAppObject)
    return app


def main() -> Any:
    """
    Launch Betty's Command-Line Interface.

    This is a stand-alone entry point that will manage an event loop and Betty application.
    """
    # Because this function creates and owns the event loop, Click cannot handle exceptions that are the result of the
    # event loop shutting down. To allow for graceful cancellations, catch any propagated KeyboardInterrupt from the
    # loop, and handle it as similar to how Click does it as possible.
    try:
        return run(_main())
    except KeyboardInterrupt:
        print("Aborted!")  # noqa T201
        sys.exit(1)


async def _main() -> Any:
    async with App.new_from_environment() as app, app:
        main_command = await new_main_command(app)
        return await main_command.main(sys.argv[1:])


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
        message=about.report(),
        prog_name="Betty",
    )
    def main_command(*args: str) -> None:
        pass  # pragma: no cover

    return main_command
