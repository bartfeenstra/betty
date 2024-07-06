"""
Provide the Command Line Interface.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from asyncio import run
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import (
    Callable,
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
from betty.cli import _discover
from betty.contextlib import SynchronizedContextManager
from betty.error import UserFacingError
from betty.locale import DEFAULT_LOCALIZER
from betty.locale.localizable import _
from betty.logging import CliHandler
from betty.project import Project
from betty.assertion.error import AssertionFailed

if TYPE_CHECKING:
    from collections.abc import Coroutine, Mapping
    from PyQt6.QtWidgets import QMainWindow


_P = ParamSpec("_P")


def discover_commands() -> Mapping[str, Command]:
    """
    Discover the available commands.
    """
    return _discover.discover_commands()


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
    f: Callable[Concatenate[App, _P], None],
) -> Callable[_P, None]:
    """
    Decorate a command to receive the currently running :py:class:`betty.app.App` as its first argument.
    """

    @wraps(f)
    def _command(*args: _P.args, **kwargs: _P.kwargs) -> None:
        ctx = get_current_context()
        _init_ctx_app(ctx)
        return f(ctx.obj["app"], *args, **kwargs)

    return _command


async def _read_project_configuration(
    project: Project, provided_configuration_file_path: str | None
) -> None:
    project_directory_path = Path.cwd()
    logger = logging.getLogger(__name__)
    if provided_configuration_file_path is None:
        try_configuration_file_paths = [
            project_directory_path / f"betty{extension}"
            for extension in {".json", ".yaml", ".yml"}
        ]
    else:
        try_configuration_file_paths = [
            project_directory_path / provided_configuration_file_path
        ]
    for try_configuration_file_path in try_configuration_file_paths:
        try:
            await project.configuration.read(try_configuration_file_path)
        except FileNotFoundError:
            continue
        else:
            logger.info(
                project.app.localizer._(
                    "Loaded the configuration from {configuration_file_path}."
                ).format(configuration_file_path=str(try_configuration_file_path)),
            )
            return

    if provided_configuration_file_path is None:
        raise AssertionFailed(
            _(
                "Could not find any of the following configuration files in {project_directory_path}: {configuration_file_names}."
            ).format(
                configuration_file_names=", ".join(
                    str(try_configuration_file_path.relative_to(project_directory_path))
                    for try_configuration_file_path in try_configuration_file_paths
                ),
                project_directory_path=str(project_directory_path),
            )
        )
    else:
        raise AssertionFailed(
            _('Configuration file "{configuration_file_path}" does not exist.').format(
                configuration_file_path=provided_configuration_file_path,
            )
        )


def pass_project(
    f: Callable[Concatenate[Project, _P], None],
) -> Callable[_P, None]:
    """
    Decorate a command to receive the currently running :py:class:`betty.project.Project` as its first argument.
    """

    def _project(
        ctx: Context, __: Parameter, configuration_file_path: str | None
    ) -> Project:
        _init_ctx_app(ctx)
        app = ctx.obj["app"]
        project = Project(app)
        wait_to_thread(_read_project_configuration(project, configuration_file_path))
        ctx.with_resource(  # type: ignore[attr-defined]
            SynchronizedContextManager(project)
        )
        return project

    return click.option(  # type: ignore[return-value]
        "--configuration",
        "-c",
        "project",
        is_eager=True,
        help="The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory.",
        callback=_project,
    )(f)


@catch_exceptions()
def _init_ctx_app(ctx: Context, __: Option | Parameter | None = None, *_: Any) -> None:
    obj = ctx.ensure_object(dict)

    if "app" in obj:
        return

    logging.getLogger().addHandler(CliHandler())
    app_factory = ctx.with_resource(  # type: ignore[attr-defined]
        SynchronizedContextManager(App.new_from_environment())
    )
    obj["app"] = ctx.with_resource(  # type: ignore[attr-defined]
        SynchronizedContextManager(app_factory)
    )


def _build_init_ctx_verbosity(
    betty_logger_level: int,
    root_logger_level: int | None = None,
) -> Callable[[Context, Option | Parameter | None, bool], None]:
    def _init_ctx_verbosity(
        _: Context,
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


@click.command(help="Clear all caches.")
@pass_app
@command
async def _clear_caches(app: App) -> None:
    await app.cache.clear()


@click.command(help="Explore a demonstration site.")
@pass_app
@command
async def _demo(app: App) -> None:
    from betty.extension.demo import DemoServer

    async with DemoServer(app=app) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)


@click.command(help="Open Betty's graphical user interface (GUI).")
@pass_project
@command
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
@command
async def _generate(project: Project) -> None:
    await load.load(project)
    await generate.generate(project)


@click.command(help="Serve a generated site.")
@pass_project
@command
async def _serve(project: Project) -> None:
    async with serve.BuiltinProjectServer(project) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)


@click.command(help="View the documentation.")
@pass_app
@command
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


class _BettyCommands(click.MultiCommand):
    @catch_exceptions()
    def list_commands(self, ctx: Context) -> list[str]:
        return list(discover_commands().keys())

    @catch_exceptions()
    def get_command(self, ctx: Context, cmd_name: str) -> Command | None:
        try:
            return discover_commands()[cmd_name]
        except KeyError:
            return None


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
