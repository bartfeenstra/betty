import pytest

from betty.content_builders.raspberry_mint_timeline import Timeline
from betty.date import Date
from betty.document import Document
from betty.entities.enclosure import Enclosure
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.presence import Presence
from betty.roles.subject import Subject
from betty.test_utils.conftest import NewIsolatedProject


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
        self, resource: object, new_isolated_project: NewIsolatedProject
    ) -> None:
        async with (
            new_isolated_project(supported_plugins=[Timeline]) as project,
            project,
        ):
            sut = await Timeline.new(project)
        assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_person(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        event = Event(id="my-first-event", date=Date(1970, 1, 1))
        resource = Person()
        Presence(resource, Subject(), event)
        async with (
            new_isolated_project(supported_plugins=[Timeline]) as project,
            project,
        ):
            sut = await Timeline.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert event.id in actual

    async def test_build_template__with_place(
        self, new_isolated_project: NewIsolatedProject
    ) -> None:
        encloses_event = Event(id="my-first-event", date=Date(1970, 1, 1))
        encloses = Place(events=[encloses_event])
        event = Event(id="my-first-event", date=Date(1970, 1, 1))
        resource = Place(events=[event])
        Enclosure(encloses=encloses, enclosed_by=resource)
        async with (
            new_isolated_project(supported_plugins=[Timeline]) as project,
            project,
        ):
            sut = await Timeline.new(project)
            actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert event.id in actual
        assert encloses_event.id in actual
