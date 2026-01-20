from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from betty.app import App
from betty.console import SystemExitCode
from betty.console.command import Command
from betty.console.command.commands.demo import Demo
from betty.plugin import PluginDefinition
from betty.project import Project
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase
from betty.test_utils.serve import NoOpServer


class TestDemoDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Demo.plugin()


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestDemo(CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return Demo(isolated_app)

    async def test_configure__minimal(
        self, mocker: MockerFixture, isolated_app: App
    ) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty.project.extension.demo.serve.DemoServer", new=NoOpServer)

        await run(isolated_app, "demo", expected_exit_code=SystemExitCode.USER_QUIT)

    async def test_configure__with_path(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        m_generate_with_cleanup = mocker.patch(
            "betty.project.extension.demo.generate_with_cleanup"
        )

        project_directory_path = tmp_path / "project"

        await run(isolated_app, "demo", "--path", str(project_directory_path))

        m_generate_with_cleanup.assert_called_once()

    async def test_configure__with_path_and_url(
        self, mocker: MockerFixture, isolated_app: App, tmp_path: Path
    ) -> None:
        m_generate_with_cleanup = mocker.patch(
            "betty.project.extension.demo.generate_with_cleanup"
        )

        project_directory_path = tmp_path / "project"
        url = "https://betty.example.com"

        await run(
            isolated_app,
            "demo",
            "--path",
            str(project_directory_path),
            "--url",
            url,
        )

        m_generate_with_cleanup.assert_called_once()
        assert len(m_generate_with_cleanup.call_args.args) == 1
        project = m_generate_with_cleanup.call_args.args[0]
        assert isinstance(project, Project)
        assert project.configuration.url == url
