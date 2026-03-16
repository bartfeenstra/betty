import pytest

from betty.app import App
from betty.date import Date
from betty.document import Document
from betty.plugins.content.raspberry_mint_timeline import Timeline
from betty.plugins.entity.enclosure import Enclosure
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.presence import Presence
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.plugins.role import Subject
from betty.project import Project


class TestTimeline:
    @pytest.mark.parametrize(
        "resource",
        [
            None,
            object(),
            Person(),
            Place(),
        ],
    )
    async def test_build_template__without_associated_events(
        self, resource: object, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Timeline.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_person(self, isolated_app: App) -> None:
        event = Event(id="E0", date=Date(1970, 1, 1))
        resource = Person()
        Presence(resource, Subject(), event)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Timeline.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert event.public_id in actual

    async def test_build_template__with_place(self, isolated_app: App) -> None:
        enclosee_event = Event(id="E0", date=Date(1970, 1, 1))
        enclosee = Place(events=[enclosee_event])
        event = Event(id="E0", date=Date(1970, 1, 1))
        resource = Place(events=[event])
        Enclosure(enclosee, resource)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await Timeline.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert event.public_id in actual
        assert enclosee_event.public_id in actual
