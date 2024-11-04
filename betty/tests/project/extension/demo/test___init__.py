from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.citation import Citation
from betty.ancestry.event import Event
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.source import Source
from betty.app import App
from betty.project import Project
from betty.project.extension.demo import Demo
from betty.project.load import load
from betty.test_utils.project.extension import ExtensionTestBase
from betty.test_utils.project.extension.demo.project import demo_project_fetcher  # noqa F401

if TYPE_CHECKING:
    from betty.fetch import Fetcher
    from pytest_mock import MockerFixture


class TestDemo(ExtensionTestBase[Demo]):
    @override
    def get_sut_class(self) -> type[Demo]:
        return Demo

    async def test_load(
        self,
        demo_project_fetcher: Fetcher,  # noqa F811
        mocker: MockerFixture,
    ) -> None:
        mocker.patch("betty.wikipedia._Populator.populate")
        async with (
            App.new_temporary(fetcher=demo_project_fetcher) as app,
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
