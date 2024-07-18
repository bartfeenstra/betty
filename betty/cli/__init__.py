"""
Provide the Command Line Interface.
"""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from typing import (
    Iterator,
    TYPE_CHECKING,
)

import click
from betty import about
from betty.asyncio import wait_to_thread
from betty.error import UserFacingError
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.logging import CliHandler
from betty.plugin import PluginRepository, PluginNotFound

if TYPE_CHECKING:
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


class _BettyCommands(click.MultiCommand):
    _bootstrapped = False
    commands: PluginRepository[Command]

    def _bootstrap(self) -> None:
        if not self._bootstrapped:
            logging.getLogger().addHandler(CliHandler())
            self._bootstrapped = True

    @catch_exceptions()
    def list_commands(self, ctx: click.Context) -> list[str]:
        from betty.cli import commands

        self._bootstrap()
        return [
            command.plugin_id()
            for command in wait_to_thread(commands.COMMAND_REPOSITORY.select())
        ]

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


@click.command(
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
