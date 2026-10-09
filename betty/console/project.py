"""
Project support for the Console.
"""

from __future__ import annotations

from asyncio import gather
from pathlib import Path
from typing import TYPE_CHECKING, Any, final

from betty.argparse import validator_to_argument_type
from betty.console import ExitCode
from betty.localizables.gettext import _
from betty.localizables.markup import JoinOr
from betty.portable.file import is_load_file
from betty.project import Project, ProjectData
from betty.user import Severity
from betty.validation import Invalid, collect
from betty.validators.path import NotFound, is_path

if TYPE_CHECKING:
    import argparse
    from collections.abc import Iterable

    from betty.app import App
    from betty.console import CommandFunction, CommandResult
    from betty.serialize import Serializer
    from betty.user.ui import Ui


@final
class NotAProjectDirectory(Invalid, FileNotFoundError):
    """
    Raised when no configuration file could be found in a directory.
    """


async def add_project_argument(
    parser: argparse.ArgumentParser,
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
        except Invalid as error:
            if not isinstance(error, NotAProjectDirectory) or required:
                await app.ui.error(
                    error,
                    _("Invalid argument {argument}: {{error}}").format(
                        argument="project"
                    ),
                )
                return ExitCode.ERROR_COMMAND
            project = None
        else:
            project = await Project.new(
                app, configuration, directory=project_configuration_file.parent
            )
        return await command_function(project=project, **kwargs)

    return _command_function_with_project_argument


async def _read_project_configuration(
    provided_configuration_file: Path | None, app: App
) -> tuple[ProjectData, Path]:
    serializers = await gather(*app.serializers)
    project_directory = Path.cwd()
    if provided_configuration_file is None:
        try_configuration_files = [
            project_directory / f"betty{extension}"
            for serializer in serializers
            for extension in serializer.media_type().extensions
        ]
        for try_configuration_file in try_configuration_files:
            try:
                return await _read_project_configuration_file(
                    try_configuration_file, serializers, app.ui
                )
            except NotFound:
                pass
        # @todo raise InvalidGroup(rel=Rel.ONE) instead?
        raise NotAProjectDirectory(
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
    project_configuration_file = (
        (project_directory / provided_configuration_file).expanduser().resolve()
    )
    with (
        collect(
            project_configuration_file, location=[project_configuration_file]
        ) as errors,
        errors.catch(),
    ):
        return await _read_project_configuration_file(
            project_configuration_file, serializers, app.ui
        )


async def _read_project_configuration_file(
    configuration_file: Path, serializers: Iterable[Serializer], ui: Ui
) -> tuple[ProjectData, Path]:
    config = ProjectData.definition.porter.load(
        is_load_file(serializers=serializers)(configuration_file)
    )
    await ui.message(
        _("Loaded the configuration from {configuration_file_path}.").format(
            configuration_file_path=str(configuration_file)
        ),
        Severity.INFO,
    )
    return config, configuration_file
