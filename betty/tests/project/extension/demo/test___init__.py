from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.project import Project
from betty.project.config import ExtensionConfiguration
from betty.project.extension.demo import Demo
from betty.project.load import load
from betty.test_utils.project.extension import ExtensionTestBase

if TYPE_CHECKING:
    from betty.app import App
    from pytest_mock import MockerFixture


class TestDemo(ExtensionTestBase[Demo]):
    @override
    def get_sut_class(self) -> type[Demo]:
        return Demo

    async def test_load(self, mocker: MockerFixture, new_temporary_app: App) -> None:
        mocker.patch("betty.wikipedia._Populator.populate")
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.append(ExtensionConfiguration(Demo))
            async with project:
                await load(project)
            assert len(project.ancestry[Person]) != 0
            assert len(project.ancestry[Place]) != 0
            assert len(project.ancestry[Event]) != 0
            assert len(project.ancestry[Source]) != 0
            assert len(project.ancestry[Citation]) != 0
