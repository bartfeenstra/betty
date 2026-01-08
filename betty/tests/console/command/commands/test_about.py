import pytest
from typing_extensions import override

from betty.app import App
from betty.console.command import Command
from betty.console.command.commands.about import About
from betty.plugin import PluginDefinition
from betty.portable.file import dump_file
from betty.project import Project
from betty.rich.user import RichUser
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.console import run
from betty.test_utils.console.command import CommandDefinitionTestBase, CommandTestBase


class TestAboutDefinition(CommandDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return About.plugin()


class TestAbout(CommandTestBase):
    @override
    @pytest.fixture
    def sut(self, isolated_app: App) -> Command:
        return About(isolated_app)

    async def test_configure(self, isolated_app_factory: IsolatedAppFactory) -> None:
        async with isolated_app_factory(user=RichUser()) as app, app:
            result = await run(app, "about")
            assert "Betty" in result.stdout

    async def test_configure__with_project(
        self, isolated_app_factory: IsolatedAppFactory
    ) -> None:
        async with (
            isolated_app_factory(user=RichUser()) as app,
            app,
            Project.new_isolated(app) as project,
        ):
            await dump_file(
                project.configuration.data().dump(project.configuration),
                project.configuration_file_path,
            )
            result = await run(
                app,
                "about",
                "--project",
                str(project.configuration_file_path),
            )
            assert "Betty" in result.stdout
