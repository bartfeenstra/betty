from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.extension.demo import Demo, generate_with_cleanup
from betty.project import Project
from betty.project.load import load
from betty.test_utils.project.extension import (
    ExtensionDefinitionTestBase,
    ExtensionTestBase,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.app import App
    from betty.extension import Extension
    from betty.plugin import PluginDefinition
    from betty.project.job import ProjectContext
    from betty.test_utils.conftest import IsolatedAppFactory


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_generate_with_cleanup__without_error(
    mocker: MockerFixture, isolated_app: App
) -> None:
    async def _generate(
        project: Project, *, job_context: ProjectContext | None = None
    ) -> None:
        project.output_directory.mkdir(parents=True)

    m_generate = mocker.patch("betty.project.generate.generate")
    m_generate.side_effect = _generate
    async with Project.new_isolated(isolated_app) as project, project:
        (project.directory / "sentinel").touch()
        await generate_with_cleanup(project)
        assert project.directory.is_dir()
        assert project.output_directory.is_dir()
        assert not (project.directory / "sentinel").exists()


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_generate_with_cleanup__with_error(
    mocker: MockerFixture, isolated_app: App
) -> None:
    error_message = "generation error"

    async def _generate(
        project: Project, *, job_context: ProjectContext | None = None
    ) -> None:
        project.output_directory.mkdir(parents=True)
        raise RuntimeError(error_message)

    m_generate = mocker.patch("betty.project.generate.generate")
    m_generate.side_effect = _generate
    async with Project.new_isolated(isolated_app) as project, project:
        with pytest.raises(RuntimeError, match=error_message):
            await generate_with_cleanup(project)
        assert not project.directory.exists()


class TestDemoDefinition(ExtensionDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Demo.plugin()


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestDemo(ExtensionTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> Extension:
        async with Project.new_isolated(isolated_app) as project, project:
            return Demo(project=project)

    async def test_load(
        self, mocker: MockerFixture, isolated_app_factory: IsolatedAppFactory
    ) -> None:
        mocker.patch("betty.wiki.populator.Populator.populate")
        async with (
            isolated_app_factory() as app,
            app,
            Project.new_isolated(app) as project,
        ):
            project.configuration.extensions.add(Demo)
            async with project:
                await load(project)
            assert len(project.ancestry[Person]) != 0
            assert len(project.ancestry[Place]) != 0
            assert len(project.ancestry[Event]) != 0
            assert len(project.ancestry[Source]) != 0
            assert len(project.ancestry[Citation]) != 0
