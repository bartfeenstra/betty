"""
Project support for the Console.
"""

import argparse
from asyncio import gather
from collections.abc import Iterable
from contextlib import suppress
from pathlib import Path
from typing import Any

from betty.app import App
from betty.argparse import assertion_to_argument_type
from betty.assertions.path import assert_path
from betty.console.command import CommandFunction
from betty.error import FileNotFound
from betty.exception import HumanFacingException
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import AnyEnumeration
from betty.portable.file import assert_load_file
from betty.project import Project, ProjectData
from betty.serde import Serializer
from betty.user import User


class ConfigurationFileNotFound(HumanFacingException):
    """
    Raised when no configuration file could be found.
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
    localizer, serializers = await gather(app.localizer, gather(*app.serializers))
    parser.add_argument(
        "-p",
        "--project",
        dest="project_configuration_file",
        help=localizer._(
            "The path to a Betty project directory or configuration file. Defaults to {default} in the current working directory."
        ).format(
            default=f"betty.{'|'.join([extension[1:] for serializer in serializers for extension in serializer.media_type().extensions])}"
        ),
        type=assertion_to_argument_type(assert_path(), localizer=localizer),
    )

    async def _command_function_with_project_argument(
        *, project_configuration_file: Path | None = None, **kwargs: Any
    ) -> None:
        project: Project | None
        try:
            (
                configuration,
                project_configuration_file,
            ) = await _read_project_configuration(project_configuration_file, app)
        except ConfigurationFileNotFound:
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
            with suppress(FileNotFound):
                return await _read_project_configuration_file(
                    try_configuration_file, serializers, app.user
                )
        raise ConfigurationFileNotFound(
            _(
                "Could not find any of the following configuration files in {project_directory_path}: {configuration_file_names}."
            ).format(
                configuration_file_names=AnyEnumeration(
                    *(
                        str(x.relative_to(project_directory))
                        for x in try_configuration_files
                    )
                ),
                project_directory_path=str(project_directory),
            )
        )
    return await _read_project_configuration_file(
        (project_directory / provided_configuration_file).expanduser().resolve(),
        serializers,
        app.user,
    )


async def _read_project_configuration_file(
    configuration_file: Path, serializers: Iterable[Serializer], user: User
) -> tuple[ProjectData, Path]:
    assert_configuration = assert_load_file(serializers=serializers)
    try:
        portable = assert_configuration(configuration_file)
    except HumanFacingException as error:
        await user.message_debug(error)
        raise
    else:
        await user.message_information_details(
            _("Loaded the configuration from {configuration_file_path}.").format(
                configuration_file_path=str(configuration_file)
            ),
        )
        return ProjectData.data().porter.load(portable), configuration_file
