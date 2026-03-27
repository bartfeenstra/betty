from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.plugins.entity.citation import Citation
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.source import Source
from betty.plugins.extension.demo import Demo, generate_with_cleanup
from betty.project.load import load

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.job import Context
    from betty.project import Project
    from betty.test_utils.conftest import IsolatedProjectFactory


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_generate_with_cleanup__without_error(
    mocker: MockerFixture, isolated_project: Project
) -> None:
    async def _generate(project: Project, *, context: Context | None = None) -> None:
        project.output_directory.mkdir(parents=True)

    m_generate = mocker.patch("betty.project.generate.generate")
    m_generate.side_effect = _generate
    (isolated_project.directory / "sentinel").touch()
    await generate_with_cleanup(isolated_project)
    assert isolated_project.directory.is_dir()
    assert isolated_project.output_directory.is_dir()
    assert not (isolated_project.directory / "sentinel").exists()


@pytest.mark.usefixtures("demo_project_aioresponses")
async def test_generate_with_cleanup__with_error(
    mocker: MockerFixture, isolated_project: Project
) -> None:
    error_message = "generation error"

    async def _generate(project: Project, *, context: Context | None = None) -> None:
        project.output_directory.mkdir(parents=True)
        raise RuntimeError(error_message)

    m_generate = mocker.patch("betty.project.generate.generate")
    m_generate.side_effect = _generate
    with pytest.raises(RuntimeError, match=error_message):
        await generate_with_cleanup(isolated_project)
    assert not isolated_project.directory.exists()


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestDemo:
    async def test_load(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        mocker.patch("betty.wiki.populator.Populator.populate")
        async with isolated_project_factory(service_plugins=[Demo]) as project:
            await load(project)
            assert len(project.ancestry[Person]) != 0
            assert len(project.ancestry[Place]) != 0
            assert len(project.ancestry[Event]) != 0
            assert len(project.ancestry[Source]) != 0
            assert len(project.ancestry[Citation]) != 0
