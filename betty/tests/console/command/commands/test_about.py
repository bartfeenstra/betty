import pytest
from typing_extensions import override

from betty.config.file import write_configuration_file
from betty.console.command.commands.about import About
from betty.console.user import ConsoleUser
from betty.plugin import PluginDefinition
from betty.project import Project
from betty.test_utils.conftest import TemporaryAppFactory
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandPluginTestBase


class TestAboutDefinition(CommandPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return About.plugin


class TestAbout:
    async def test_configure(self, temporary_app_factory: TemporaryAppFactory) -> None:
        async with temporary_app_factory(user=ConsoleUser()) as app, app:
            result = await run(app, "about")
            assert "Betty" in result.stdout

    async def test_configure__with_project(
        self, temporary_app_factory: TemporaryAppFactory
    ) -> None:
        async with (
            temporary_app_factory(user=ConsoleUser()) as app,
            app,
            Project.new_temporary(app) as project,
        ):
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            result = await run(
                app,
                "about",
                "--project",
                str(project.configuration.configuration_file_path),
            )
            assert "Betty" in result.stdout
