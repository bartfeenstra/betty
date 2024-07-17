"""
Provide the Command Line Interface.
"""

from __future__ import annotations

import logging
from asyncio import run
from functools import wraps
from importlib import metadata
from pathlib import Path
from typing import Any, Concatenate, ParamSpec, ClassVar, TYPE_CHECKING, Mapping

import click
from click import get_current_context, Context, option, Option, Parameter
from typing_extensions import override

from betty import about
from betty.app import App
from betty.assertion.error import AssertionFailed
from betty.asyncio import wait_to_thread
from betty.cli import catch_exceptions
from betty.config import assert_configuration_file
from betty.contextlib import SynchronizedContextManager
from betty.locale.localizable import _, Localizable, plain
from betty.plugin import Plugin, PluginId, PluginRepository
from betty.plugin.lazy import LazyPluginRepositoryBase
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

_P = ParamSpec("_P")


class Command(Plugin):
    """
    Define a CLI command plugin.

    Read more about :doc:`/development/plugin/command`.
    """

    _click_command: ClassVar[click.Command]

    @classmethod
    def click_command(cls) -> click.Command:
        """
        Get the plugin's Click command.
        """
        return cls._click_command

    @override
    @classmethod
    def plugin_id(cls) -> PluginId:
        return cls.click_command().name

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain(cls.click_command().name)

    @override
    @classmethod
    def plugin_description(cls) -> Localizable | None:
        command_help = cls.click_command().short_help
        if command_help is None:
            return None
        return plain(command_help)


class _CommandRepository(LazyPluginRepositoryBase[Command]):
    """
    Discover and manage CLI commands.
    """

    async def _load_plugins(self) -> Mapping[str, type[Command]]:
        plugins = self._load_plugins_group("betty.command")
        if await about.is_development():
            plugins = {**plugins, **(self._load_plugins_group("betty.dev.command"))}
        return plugins

    def _load_plugins_group(
        self, entry_point_group: str
    ) -> Mapping[str, type[Command]]:
        plugins = {}
        for entry_point in metadata.entry_points(
            group=entry_point_group,
        ):

            class _Command(Command):
                _click_command = entry_point.load()

            plugins[_Command.plugin_id()] = _Command
        return plugins


COMMAND_REPOSITORY: PluginRepository[Command] = _CommandRepository()
"""
The Command Line Interface command repository.

Read more about :doc:`/development/plugin/command`.
"""


def _command_build_init_ctx_verbosity(
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


def command(
    f: Callable[_P, Coroutine[Any, Any, None]],
) -> Callable[Concatenate[_P], None]:
    """
    Mark something a Betty command.
    """

    @wraps(f)
    @catch_exceptions()
    @click.option(
        "-v",
        "--verbose",
        is_eager=True,
        default=False,
        is_flag=True,
        expose_value=False,
        help="Show verbose output, including informative log messages.",
        callback=_command_build_init_ctx_verbosity(logging.INFO),
    )
    @click.option(
        "-vv",
        "--more-verbose",
        "more_verbose",
        is_eager=True,
        default=False,
        is_flag=True,
        expose_value=False,
        help="Show more verbose output, including debug log messages.",
        callback=_command_build_init_ctx_verbosity(logging.DEBUG),
    )
    @click.option(
        "-vvv",
        "--most-verbose",
        "most_verbose",
        is_eager=True,
        default=False,
        is_flag=True,
        expose_value=False,
        help="Show most verbose output, including all log messages.",
        callback=_command_build_init_ctx_verbosity(logging.NOTSET, logging.NOTSET),
    )
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
            for extension in (".json", ".yaml", ".yml")
        ]
    else:
        try_configuration_file_paths = [
            project_directory_path / provided_configuration_file_path
        ]
    assert_configuration = assert_configuration_file(project.configuration)
    for try_configuration_file_path in try_configuration_file_paths:
        try:
            assert_configuration(try_configuration_file_path)
            project.configuration.configuration_file_path = try_configuration_file_path
        except AssertionFailed:
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
        project: Project = ctx.with_resource(  # type: ignore[attr-defined]
            SynchronizedContextManager(Project.new_temporary(app))
        )
        wait_to_thread(_read_project_configuration(project, configuration_file_path))
        ctx.with_resource(  # type: ignore[attr-defined]
            SynchronizedContextManager(project)
        )
        return project

    return option(  # type: ignore[return-value]
        "--configuration",
        "-c",
        "project",
        help="The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory.",
        callback=_project,
    )(f)


@catch_exceptions()
def _init_ctx_app(ctx: Context, __: Option | Parameter | None = None, *_: Any) -> None:
    obj = ctx.ensure_object(dict)

    if "app" in obj:
        return

    app_factory = ctx.with_resource(  # type: ignore[attr-defined]
        SynchronizedContextManager(App.new_from_environment())
    )
    obj["app"] = ctx.with_resource(  # type: ignore[attr-defined]
        SynchronizedContextManager(app_factory)
    )
