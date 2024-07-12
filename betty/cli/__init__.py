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
    from collections.abc import Callable
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


def _build_init_ctx_verbosity(
    betty_logger_level: int,
    root_logger_level: int | None = None,
) -> Callable[[click.Context, click.Option | click.Parameter | None, bool], None]:
    def _init_ctx_verbosity(
        _: click.Context,
        __: click.Option | click.Parameter | None = None,
        is_verbose: bool = False,
    ) -> None:
        if is_verbose:
            for logger_name, logger_level in (
                ("betty", betty_logger_level),
                (None, root_logger_level),
            ):
                logger = logging.getLogger(logger_name)
                if (
                    logger_level is not None
                    and logger.getEffectiveLevel() > logger_level
                ):
                    logger.setLevel(logger_level)

    return _init_ctx_verbosity


@click.command(
    cls=_BettyCommands,
    # Set an empty help text so Click does not automatically use the function's docstring.
    help="",
)
@click.option(
    "-v",
    "--verbose",
    is_eager=True,
    default=False,
    is_flag=True,
    help="Show verbose output, including informative log messages.",
    callback=_build_init_ctx_verbosity(logging.INFO),
)
@click.option(
    "-vv",
    "--more-verbose",
    "more_verbose",
    is_eager=True,
    default=False,
    is_flag=True,
    help="Show more verbose output, including debug log messages.",
    callback=_build_init_ctx_verbosity(logging.DEBUG),
)
@click.option(
    "-vvv",
    "--most-verbose",
    "most_verbose",
    is_eager=True,
    default=False,
    is_flag=True,
    help="Show most verbose output, including all log messages.",
    callback=_build_init_ctx_verbosity(logging.NOTSET, logging.NOTSET),
)
@click.version_option(
    wait_to_thread(about.version_label()),
    message=wait_to_thread(about.report()),
    prog_name="Betty",
)
def main(verbose: bool, more_verbose: bool, most_verbose: bool) -> None:
    """
    Launch Betty's Command-Line Interface.
    """
    pass  # pragma: no cover
