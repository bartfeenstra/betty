from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.load import load
from betty.loaders.demo import Demo
from betty.project import Project

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.test_utils.conftest import NewIsolatedProject


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestDemo:
    async def test_load(
        self, mocker: MockerFixture, new_isolated_project: NewIsolatedProject
    ) -> None:
        mocker.patch("betty.wiki.populator.Populator.populate")
        async with new_isolated_project() as project:
            Project.loaders.add_init_plugins(project, Demo)
            async with project:
                await load(project)
                assert len(project.ancestry[Person]) != 0
                assert len(project.ancestry[Place]) != 0
                assert len(project.ancestry[Event]) != 0
                assert len(project.ancestry[Source]) != 0
                assert len(project.ancestry[Citation]) != 0
