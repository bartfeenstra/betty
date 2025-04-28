"""
Provide the Command Line Interface.
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from contextlib import suppress
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, Concatenate, ParamSpec, TypeVar, cast, overload

import asyncclick as click

from betty import about
from betty.assertion import assert_none, assert_or, assert_path
from betty.assertion.error import AssertionFailed
from betty.cli.error import user_facing_error_to_bad_parameter
from betty.config import assert_configuration_file
from betty.error import FileNotFound, UserFacingError
from betty.locale.localizable import _
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository
from betty.plugin.proxy import ProxyPluginRepository
from betty.project import Project
from betty.project.config import ProjectConfiguration
from betty.serde.format import FORMAT_REPOSITORY

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from betty.cli import ContextAppObject

_T = TypeVar("_T")
_P = ParamSpec("_P")


class Command(Plugin):
    """
    Define a CLI command plugin.

    Read more about :doc:`/development/plugin/command`.
    """

    @abstractmethod
    async def click_command(self) -> click.Command:
        """
        Get the plugin's Click command.
        """


COMMAND_REPOSITORY: PluginRepository[Command] = ProxyPluginRepository(
    EntryPointPluginRepository("betty.command"),
    *(
        [EntryPointPluginRepository("betty.dev.command")]
        if about.is_development()
        else []
    ),
)
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


@overload
def command(
    name: Callable[..., Coroutine[Any, Any, Any]],
) -> click.Command:
    pass


@overload
def command(
    name: str | None,
    **attrs: Any,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], click.Command]:
    pass


@overload
def command(
    name: None = None,
    **attrs: Any,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], click.Command]:
    pass


@overload
def command(
    name: str | None = None,
    **attrs: Any,
) -> Callable[[Callable[..., Coroutine[Any, Any, Any]]], click.Command]:
    pass


def command(
    name: str | None | Callable[..., Coroutine[Any, Any, Any]] = None,
    **attrs: Any,
) -> click.Command | Callable[[Callable[..., Coroutine[Any, Any, Any]]], click.Command]:
    """
    Mark something a Betty command.

    This is almost identical to :py:func:`asyncclick.command`.

    Functions decorated with ``@command`` may choose to raise :py:class:`betty.error.UserFacingError`, which will
    automatically be localized and reraised as :py:class:`asyncclick.ClickException`.

    Read more about :doc:`/development/plugin/command`.
    """

    def decorator(f: Callable[_P, Coroutine[Any, Any, Any]]) -> click.Command:
        @click.command(cast(str | None, name), **attrs)
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
        @click.pass_obj
        @wraps(f)
        async def _command(
            obj: ContextAppObject, *args: _P.args, **kwargs: _P.kwargs
        ) -> Any:
            try:
                return await f(*args, **kwargs)
            except UserFacingError as error:
                raise click.ClickException(error.localize(obj.localizer)) from error

        return cast(click.Command, _command)

    if callable(name):
        return decorator(name)
    return decorator


_ReturnT = TypeVar("_ReturnT")


def parameter_callback(
    f: Callable[Concatenate[_T, _P], _ReturnT], *args: _P.args, **kwargs: _P.kwargs
) -> Callable[[click.Context, click.Parameter, _T], _ReturnT]:
    """
    Convert a callback that takes a parameter (option, argument) value and returns it after processing.

    This handles errors so Click can gracefully exit.
    """
    from betty.cli import ctx_app_object

    def _callback(ctx: click.Context, __: click.Parameter, value: _T) -> _ReturnT:
        with user_facing_error_to_bad_parameter(ctx_app_object(ctx).localizer):
            return f(value, *args, **kwargs)

    return _callback


async def _read_project_configuration(
    project: Project, provided_configuration_file_path_str: Path | None
) -> None:
    project_directory_path = Path.cwd()
    if provided_configuration_file_path_str is None:
        try_configuration_file_paths = [
            project_directory_path / f"betty{extension}"
            for extension in await FORMAT_REPOSITORY.extensions()
        ]
        for try_configuration_file_path in try_configuration_file_paths:
            with suppress(FileNotFound):
                return await _read_project_configuration_file(
                    project, try_configuration_file_path
                )
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
    await _read_project_configuration_file(
        project,
        (project_directory_path / provided_configuration_file_path_str)
        .expanduser()
        .resolve(),
    )
    return None


async def _read_project_configuration_file(
    project: Project, configuration_file_path: Path
) -> None:
    localizer = await project.app.localizer
    logger = logging.getLogger(__name__)
    assert_configuration = await assert_configuration_file(project.configuration)
    try:
        assert_configuration(configuration_file_path)
    except UserFacingError as error:
        logger.debug(error.localize(localizer))
        raise
    else:
        project.configuration.configuration_file_path = configuration_file_path
        logger.info(
            localizer._(
                "Loaded the configuration from {configuration_file_path}."
            ).format(configuration_file_path=str(configuration_file_path)),
        )


def project_option(
    f: Callable[Concatenate[Project, _P], Coroutine[Any, Any, _ReturnT]],
) -> Callable[_P, Coroutine[Any, Any, _ReturnT]]:
    """
    Decorate a command that requires a :py:class:`betty.project.Project`.
    """

    @click.option(
        "--configuration",
        "-c",
        "configuration_file_path",
        help="The path to a Betty project configuration file. Defaults to betty.json|yaml|yml in the current working directory.",
        callback=parameter_callback(assert_or(assert_path(), assert_none())),
    )
    @click.pass_obj
    @wraps(f)
    async def _project_option(
        obj: ContextAppObject,
        *args: Any,
        configuration_file_path: Path | None,
        **kwargs: Any,
    ) -> _ReturnT:
        project = await Project.new(
            obj.app, configuration=await ProjectConfiguration.new(Path())
        )
        await _read_project_configuration(project, configuration_file_path)
        async with project:
            return await f(project, *args, **kwargs)

    return _project_option  # type: ignore[return-value]
