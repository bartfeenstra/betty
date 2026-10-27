from __future__ import annotations

from typing import TYPE_CHECKING, cast, override

import pytest

from betty.associations.to_one import MissingAssociate, Placeholder
from betty.date import Date
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.place_name import PlaceName
from betty.entities.presence import Presence
from betty.entity import Entity
from betty.event_types.unknown import UnknownEventType
from betty.localizer import default_localizer
from betty.privacy import Privacy
from betty.roles.subject import Subject
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestEvent(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            Event(),
            Event(description="My First Event"),
            Event(
                description="My First Event",
                presences=[Presence(Person(), Subject(), Placeholder)],
            ),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> Entity:
        return cast(Entity, request.param)

    def test___init____with_place(self) -> None:
        place = Place()
        sut = Event(place=place)
        assert sut.place is place

    def test___init____with_presences(self) -> None:
        presence = Presence(Person(), Subject(), Placeholder)
        sut = Event(presences=[presence])
        assert presence in sut.presences
        assert presence.event is sut

    def test___init____with_name(self) -> None:
        name = "The Event"
        sut = Event(name=name)
        assert sut.name is not None
        assert sut.name.localize(default_localizer) == name

    def test_id(self) -> None:
        sut = Event(
            id="my-first-event",
            event_type=UnknownEventType(),
        )
        assert sut.id == "my-first-event"

    def test_place(self) -> None:
        place = Place(
            id="my-first-place",
            names=[PlaceName("one")],
        )
        sut = Event(event_type=UnknownEventType())
        sut.place = place
        assert sut.place == place
        assert sut in place.events
        sut.place = None
        assert sut.place is None
        assert sut not in place.events

    def test_presences(self) -> None:
        person = Person()
        sut = Event(event_type=UnknownEventType())
        presence = Presence(person, Subject(), sut)
        sut.presences.add(presence)
        assert list(sut.presences) == [presence]
        assert sut == presence.event
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        with pytest.raises(MissingAssociate):
            presence.event  # noqa: B018

    def test_date(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert sut.date is None
        date = Date()
        sut.date = date
        assert sut.date == date

    def test_file_references(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert list(sut.files) == []

    def test_citations(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert list(sut.citations) == []

    def test_description(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert not sut.description

    def test_private(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert sut.privacy is Privacy.UNDETERMINED

    def test_event_type(self) -> None:
        event_type = UnknownEventType()
        sut = Event(event_type=event_type)
        assert sut.event_type is event_type

    def test_name(self) -> None:
        name = "The Event"
        sut = Event()
        sut.name = name
        assert sut.name is not None
        assert sut.name.localize(default_localizer) == name
