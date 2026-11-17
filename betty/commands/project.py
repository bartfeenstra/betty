"""
Project support for consoles.
"""

from __future__ import annotations

from asyncio import gather
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any

from betty.argparse import validator_to_argument_type
from betty.file import read
from betty.localizables.gettext import _
from betty.localizables.markup import JoinOr
from betty.project import Project, ProjectConfig
from betty.serialize import serializer_for
from betty.user import Severity
from betty.validation import Invalid
from betty.validators.path import NotFound, is_path
from betty.validators.portable import is_portable_data

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from collections.abc import Iterable

    from betty.app import App
    from betty.console import CommandFunction, CommandResult
    from betty.serialize import Serializer
    from betty.user.ui import Ui


# @todo Do we use this, or should we?
class ProjectConfigurationNotFound(Invalid):
    """
    Raised when no configuration file could be found.
    """


async def add_project_argument(
    parser: ArgumentParser,
    command_function: CommandFunction,
    app: App,
    *,
    required: bool = True,
) -> CommandFunction:
    """
    Add an argument to load a :py:class:`betty.project.Project` into a ``project`` keyword argument.
    """
    serializers = await gather(*app.serializers)
    parser.add_argument(
        "-p",
        "--project",
        dest="project_configuration_file",
        help=app.ui.localizer.translate._(
            "The path to a Betty project directory or configuration file. Defaults to {default} in the current working directory."
        ).format(
            default=f"betty.{'|'.join([extension[1:] for serializer in serializers for extension in serializer.media_type().extensions])}"
        ),
        type=validator_to_argument_type(is_path),
    )

    async def _command_function_with_project_argument(
        *, project_configuration_file: Path | None = None, **kwargs: Any
    ) -> CommandResult:
        project: Project | None
        try:
            (
                configuration,
                project_configuration_file,
            ) = await _read_project_configuration(project_configuration_file, app)
        except ProjectConfigurationNotFound:
            if required:
                raise
            project = None
        else:
            project = await Project.new(
                app, configuration, directory=project_configuration_file.parent
            )
        return await command_function(project=project, **kwargs)

    return _command_function_with_project_argument


async def _read_project_configuration(
    provided_configuration_file: Path | None, app: App
) -> tuple[ProjectConfig, Path]:
    serializers = await gather(*app.serializers)
    project_directory = Path.cwd()
    if provided_configuration_file is None:
        try_configuration_files = [
            project_directory / f"betty{extension}"
            for serializer in serializers
            for extension in serializer.media_type().extensions
        ]
        for try_configuration_file in try_configuration_files:
            with suppress(NotFound):
                return await _read_project_configuration_file(
                    try_configuration_file, serializers, app.ui
                )
        raise ProjectConfigurationNotFound(
            project_directory,
            message=_(
                "Could not find any of the following configuration files in {project_directory_path}: {configuration_file_names}."
            ).format(
                configuration_file_names=JoinOr(
                    *(
                        str(x.relative_to(project_directory))
                        for x in try_configuration_files
                    )
                ),
                project_directory_path=str(project_directory),
            ),
        )
    return await _read_project_configuration_file(
        (project_directory / provided_configuration_file).expanduser().resolve(),
        serializers,
        app.ui,
    )


async def _read_project_configuration_file(
    configuration_file: Path, serializers: Iterable[Serializer], ui: Ui
) -> tuple[ProjectConfig, Path]:
    try:
        config_data = await read(configuration_file)
    except NotFound as error:
        await ui.message(error, Severity.DEBUG)
        raise
    dumped_config = is_portable_data(
        serializer_for(serializers, configuration_file.name).load(config_data)
    )
    await ui.message(
        _("Loaded the configuration from {configuration_file_path}.").format(
            configuration_file_path=str(configuration_file)
        ),
        Severity.INFO,
    )
    return ProjectConfig.definition.porter.load(dumped_config), configuration_file
