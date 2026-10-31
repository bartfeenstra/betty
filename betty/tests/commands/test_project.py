import json
from argparse import ArgumentParser
from contextlib import chdir
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from betty.app import App
from betty.commands.project import add_project_argument
from betty.console import CommandResult, call_command_func
from betty.exception import HumanFacingException
from betty.file import write
from betty.project import Project
from betty.sys import ExitCode
from betty.typing import Unreachable

if TYPE_CHECKING:
    from betty.portable import PortableMapping


async def test_add_project_argument__with_argument(
    isolated_app: App, tmp_path: Path
) -> None:
    configuration: PortableMapping = {
        "title": "Betty",
        "url": "https://example.com",
    }
    configuration_file = tmp_path / "betty.json"
    parser = ArgumentParser()

    async def _command_function(*, project: Project) -> CommandResult:
        assert project.directory == tmp_path

    command_function = await add_project_argument(
        parser, _command_function, isolated_app
    )
    await write(configuration_file, json.dumps(configuration))
    namespace = parser.parse_args(["--project", str(configuration_file)])
    assert namespace.project_configuration_file == configuration_file
    assert await call_command_func(command_function, namespace) is ExitCode.OK


async def test_add_project_argument__without_argument_with_file(
    isolated_app: App, tmp_path: Path
) -> None:
    configuration: PortableMapping = {
        "title": "Betty",
        "url": "https://example.com",
    }
    configuration_file = tmp_path / "betty.json"
    parser = ArgumentParser()

    async def _command_function(*, project: Project) -> CommandResult:
        assert project.directory == tmp_path

    command_function = await add_project_argument(
        parser, _command_function, isolated_app
    )
    await write(configuration_file, json.dumps(configuration))
    namespace = parser.parse_args([])
    assert namespace.project_configuration_file is None
    with chdir(tmp_path):
        assert await call_command_func(command_function, namespace) is ExitCode.OK


async def test_add_project_argument__without_argument_without_file(
    isolated_app: App, tmp_path: Path
) -> None:
    parser = ArgumentParser()

    async def _command_function(*, project: Project) -> CommandResult:
        raise Unreachable

    command_function = await add_project_argument(
        parser, _command_function, isolated_app
    )
    namespace = parser.parse_args([])
    assert namespace.project_configuration_file is None
    with chdir(tmp_path), pytest.raises(HumanFacingException):
        assert await call_command_func(command_function, namespace) is ExitCode.OK
