"""
Provide the Command Line Interface.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from asyncio import run
from contextlib import suppress, contextmanager
from functools import wraps
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import (
    Callable,
    cast,
    Iterator,
    ParamSpec,
    Concatenate,
    TYPE_CHECKING,
    Any,
)

import click
from click import get_current_context, Context, Option, Command, Parameter

from betty import about, generate, load, documentation, locale, serve
from betty.app import App
from betty.asyncio import wait_to_thread
from betty.contextlib import SynchronizedContextManager
from betty.error import UserFacingError
from betty.importlib import import_any
from betty.locale import DEFAULT_LOCALIZER
from betty.logging import CliHandler

if TYPE_CHECKING:
    from betty.project.__init__ import Project
    from collections.abc import Coroutine, Sequence, Mapping
    from PyQt6.QtWidgets import QMainWindow


_P = ParamSpec("_P")


def discover_commands() -> Mapping[str, type[Command]]:
    """
    Gather the available extension types.
    """
    betty_entry_points: Sequence[EntryPoint]
    betty_entry_points = entry_points(  # type: ignore[assignment, unused-ignore]
        group="betty.command",  # type: ignore[call-arg, unused-ignore]
    )
    return {
        betty_entry_point.name: import_any(betty_entry_point.value)
        for betty_entry_point in betty_entry_points
    }


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


def command(f: Callable[_P, Coroutine[Any, Any, None]]) -> Callable[_P, None]:
    """
    Mark something a Betty command.
    """

    @wraps(f)
    @catch_exceptions()
    def _command(*args: _P.args, **kwargs: _P.kwargs) -> None:
        return run(f(*args, **kwargs))

    return _command


def pass_app(
    f: Callable[Concatenate[App, _P], Any],
) -> Callable[_P, Any]:
    """
    Decorate a command to receive the currently running :py:class:`betty.app.App` as its first argument.
    """

    @wraps(f)
    @catch_exceptions()
    def _command(*args: _P.args, **kwargs: _P.kwargs) -> None:
        return f(get_current_context().obj["app"], *args, **kwargs)

    return _command


def pass_project(
    f: Callable[Concatenate[App, _P], Any],
) -> Callable[_P, Any]:
    """
    Decorate a command to receive the currently running :py:class:`betty.app.Project` as its first argument.
    """

    @wraps(f)
    @catch_exceptions()
    @click.option(
        "--configuration",
        "-c",
        "configuration_file_path",
        is_eager=True,
        help="The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory.",
        # @todo Actually create a project
        callback=lambda _, __, configuration_file_path: (
            Path(configuration_file_path) if configuration_file_path else None
        ),
    )
    def _command(*args: _P.args, **kwargs: _P.kwargs) -> None:
        # @todo Actully pass on the project
        return f(get_current_context().obj["app"], *args, **kwargs)

    return _command


@catch_exceptions()
def _init_ctx_app(ctx: Context, __: Option | Parameter | None = None, *_: Any) -> None:
    run(__init_ctx_app(ctx))


async def __init_ctx_app(ctx: Context) -> None:
    ctx.ensure_object(dict)

    if "initialized" in ctx.obj:
        return
    ctx.obj["initialized"] = True

    logging.getLogger().addHandler(CliHandler())

    app = ctx.with_resource(  # type: ignore[attr-defined]
        SynchronizedContextManager(App.new_from_environment())
    )
    ctx.obj["commands"] = {
        **discover_commands(),
        "docs": _docs,
        "clear-caches": _clear_caches,
        "demo": _demo,
        "generate": _generate,
        "serve": _serve,
    }
    if await about.is_development():
        ctx.obj["commands"]["init-translation"] = _init_translation
        ctx.obj["commands"]["update-translations"] = _update_translations
    ctx.obj["app"] = app


def _build_init_ctx_verbosity(
    betty_logger_level: int,
    root_logger_level: int | None = None,
) -> Callable[[Context, Option | Parameter | None, bool], None]:
    def _init_ctx_verbosity(
        ctx: Context,
        __: Option | Parameter | None = None,
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


class _BettyCommands(click.MultiCommand):
    @catch_exceptions()
    def list_commands(self, ctx: Context) -> list[str]:
        _init_ctx_app(ctx)
        return list(ctx.obj["commands"].keys())

    @catch_exceptions()
    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        _init_ctx_app(ctx)
        with suppress(KeyError):
            return cast(Command, ctx.obj["commands"][cmd_name])
        return None


@click.command(
    cls=_BettyCommands,
    # Set an empty help text so Click does not automatically use the function's docstring.
    help="",
)
@click.option(
    "--configuration",
    "-c",
    "app",
    is_eager=True,
    help="The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory. This will make additional commands available.",
    callback=_init_ctx_app,
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
def main(app: App, verbose: bool, more_verbose: bool, most_verbose: bool) -> None:
    """
    Launch Betty's Command-Line Interface.
    """
    pass  # pragma: no cover


@click.command(help="Clear all caches.")
@pass_app
async def _clear_caches(app: App) -> None:
    await app.cache.clear()


@click.command(help="Explore a demonstration site.")
@pass_app
async def _demo(app: App) -> None:
    from betty.extension.demo import DemoServer

    async with DemoServer(app=app) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)


@click.command(help="Open Betty's graphical user interface (GUI).")
@pass_project
async def _gui(project: Project, configuration_file_path: Path | None) -> None:
    from betty.gui import BettyApplication
    from betty.gui.app import WelcomeWindow
    from betty.gui.project import ProjectWindow

    async with BettyApplication([sys.argv[0]]).with_app(project.app) as qapp:
        window: QMainWindow
        if configuration_file_path is None:
            window = WelcomeWindow(project.app)
        else:
            await project.configuration.read(configuration_file_path)
            window = ProjectWindow(project)
        window.show()
        sys.exit(qapp.exec())


@click.command(help="Generate a static site.")
@pass_project
async def _generate(project: Project) -> None:
    await load.load(project)
    await generate.generate(project)


@click.command(help="Serve a generated site.")
@pass_project
async def _serve(project: Project) -> None:
    async with serve.BuiltinProjectServer(project) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)


@click.command(help="View the documentation.")
@pass_app
async def _docs(app: App):
    server = documentation.DocumentationServer(
        app.binary_file_cache.path,
        localizer=app.localizer,
    )
    async with server:
        await server.show()
        while True:
            await asyncio.sleep(999)


@click.command(
    short_help="Initialize a new translation",
    help="Initialize a new translation.\n\nThis is available only when developing Betty.",
)
@click.argument("locale")
@command
async def _init_translation(locale: str) -> None:
    from betty.locale import init_translation

    await init_translation(locale)


@click.command(
    short_help="Update all existing translations",
    help="Update all existing translations.\n\nThis is available only when developing Betty.",
)
@command
async def _update_translations() -> None:
    await locale.update_translations()
