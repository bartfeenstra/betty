from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.project import Project, ProjectContext
from betty.project.extension.demo import Demo, generate_with_cleanup
from betty.project.load import load
from betty.test_utils.project.extension import (
    ExtensionPluginTestBase,
    ExtensionTestBase,
)
from betty.test_utils.project.extension.demo.project import (
    demo_project_aioresponses,  # noqa F401
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.app import App
    from betty.plugin import PluginDefinition
    from betty.project.extension import Extension
    from betty.test_utils.conftest import TemporaryAppFactory


async def test_generate_with_cleanup__without_error(
    mocker: MockerFixture, temporary_app: App
) -> None:
    async def _generate(
        project: Project, *, job_context: ProjectContext | None = None
    ) -> None:
        project.configuration.output_directory_path.mkdir(parents=True)

    m_generate = mocker.patch("betty.project.generate.generate")
    m_generate.side_effect = _generate
    async with Project.new_temporary(temporary_app) as project, project:
        (project.configuration.project_directory_path / "sentinel").touch()
        await generate_with_cleanup(project)
        assert project.configuration.project_directory_path.is_dir()
        assert project.configuration.output_directory_path.is_dir()
        assert not (project.configuration.project_directory_path / "sentinel").exists()


async def test_generate_with_cleanup__with_error(
    mocker: MockerFixture, temporary_app: App
) -> None:
    error_message = "generation error"

    async def _generate(
        project: Project, *, job_context: ProjectContext | None = None
    ) -> None:
        project.configuration.output_directory_path.mkdir(parents=True)
        raise RuntimeError(error_message)

    m_generate = mocker.patch("betty.project.generate.generate")
    m_generate.side_effect = _generate
    async with Project.new_temporary(temporary_app) as project, project:
        with pytest.raises(RuntimeError, match=error_message):
            await generate_with_cleanup(project)
        assert not project.configuration.project_directory_path.exists()


class TestDemoDefinition(ExtensionPluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Demo.plugin


class TestDemo(ExtensionTestBase):
    @override
    @pytest.fixture
    async def sut(self, temporary_app: App) -> Extension:
        async with Project.new_temporary(temporary_app) as project, project:
            return Demo(project)

    async def test_load(
        self,
        demo_project_aioresponses: None,  # noqa F811
        mocker: MockerFixture,
        temporary_app_factory: TemporaryAppFactory,
    ) -> None:
        mocker.patch("betty.wiki.populator.Populator.populate")
        async with (
            temporary_app_factory() as app,
            app,
            Project.new_temporary(app) as project,
        ):
            project.configuration.extensions.enable(Demo)
            async with project:
                await load(project)
            assert len(project.ancestry[Person]) != 0
            assert len(project.ancestry[Place]) != 0
            assert len(project.ancestry[Event]) != 0
            assert len(project.ancestry[Source]) != 0
            assert len(project.ancestry[Citation]) != 0
