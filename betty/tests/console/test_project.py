import argparse
import json
from contextlib import chdir
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import pytest

from betty.app import App
from betty.console import call_command_func
from betty.console.project import add_project_argument
from betty.exception import HumanFacingException
from betty.project import Project

if TYPE_CHECKING:
    from betty.serde.dump import Dump, DumpMapping


async def test_add_project_argument__with_argument(
    isolated_app: App, tmp_path: Path
) -> None:
    configuration: DumpMapping[Dump] = {
        "title": "Betty",
        "url": "https://example.com",
    }
    configuration_file_path = tmp_path / "betty.json"
    parser = argparse.ArgumentParser()

    async def _command_function(*, project: Project) -> None:
        assert project.configuration_file_path == configuration_file_path

    command_function = await add_project_argument(
        parser, _command_function, isolated_app
    )
    async with aiofiles.open(configuration_file_path, "w") as f:
        await f.write(json.dumps(configuration))
    namespace = parser.parse_args(["--project", str(configuration_file_path)])
    assert namespace.project_configuration_file_path == configuration_file_path
    await call_command_func(command_function, namespace)


async def test_add_project_argument__without_argument_with_file(
    isolated_app: App, tmp_path: Path
) -> None:
    configuration: DumpMapping[Dump] = {
        "title": "Betty",
        "url": "https://example.com",
    }
    configuration_file_path = tmp_path / "betty.json"
    parser = argparse.ArgumentParser()

    async def _command_function(*, project: Project) -> None:
        assert project.configuration_file_path == configuration_file_path

    command_function = await add_project_argument(
        parser, _command_function, isolated_app
    )
    async with aiofiles.open(configuration_file_path, "w") as f:
        await f.write(json.dumps(configuration))
    namespace = parser.parse_args([])
    assert namespace.project_configuration_file_path is None
    with chdir(tmp_path):
        await call_command_func(command_function, namespace)


async def test_add_project_argument__without_argument_without_file(
    isolated_app: App, tmp_path: Path
) -> None:
    parser = argparse.ArgumentParser()

    async def _command_function(*, project: Project) -> None:
        pass  # pragma: no cover

    command_function = await add_project_argument(
        parser, _command_function, isolated_app
    )
    namespace = parser.parse_args([])
    assert namespace.project_configuration_file_path is None
    with chdir(tmp_path), pytest.raises(HumanFacingException):
        await call_command_func(command_function, namespace)
