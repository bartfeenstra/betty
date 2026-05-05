from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from betty.date import Date, DateRange
from betty.entity import Entity
from betty.entity.association import AssociationRequired, TemporaryToOneResolver
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.place_name import PlaceName
from betty.plugins.entity.presence import Presence
from betty.plugins.entity.source import Source
from betty.plugins.event_type.birth import Birth
from betty.plugins.event_type.unknown import Unknown as UnknownEventType
from betty.plugins.role.subject import Subject
from betty.privacy import Privacy
from betty.test_utils.entity import EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.test_utils.conftest import AssertDumpsLinkedData

import pytest


class TestEvent(EntityTestBase):
    @staticmethod
    def _sut_params() -> Sequence[Entity]:
        return [
            Event(),
            Event(description="My First Event"),
            Event(
                description="My First Event",
                presences=[Presence(Person(), Subject(), TemporaryToOneResolver())],
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
        presence = Presence(Person(), Subject(), TemporaryToOneResolver())
        sut = Event(presences=[presence])
        assert presence in sut.presences
        assert presence.event is sut

    def test___init____with_name(self) -> None:
        name = "The Event"
        sut = Event(name=name)
        assert sut.name is not None
        assert sut.name.localize(DEFAULT_LOCALIZER) == name

    def test_id(self) -> None:
        event_id = "E1"
        sut = Event(
            id=event_id,
            event_type=UnknownEventType(),
        )
        assert sut.id == event_id

    def test_place(self) -> None:
        place = Place(
            id="1",
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
        person = Person(id="P1")
        sut = Event(event_type=UnknownEventType())
        presence = Presence(person, Subject(), sut)
        sut.presences.add(presence)
        assert list(sut.presences) == [presence]
        assert sut == presence.event
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        with pytest.raises(AssociationRequired):
            presence.event  # noqa: B018

    def test_date(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert sut.date is None
        date = Date()
        sut.date = date
        assert sut.date == date

    def test_file_references(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert list(sut.file_references) == []

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
        assert sut.name.localize(DEFAULT_LOCALIZER) == name

    async def test_dump_linked_data__should_dump_minimal(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "description": "https://schema.org/description",
                "place": "https://schema.org/location",
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "privacy": False,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [],
            "fileReferences": [],
            "place": None,
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="the_place",
                names=[PlaceName("The Place")],
            ),
            name="The Event",
            description="The Event Description",
        )
        presence = Presence(Person(id="the_person"), Subject(), event)
        event.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "description": "https://schema.org/description",
                "place": "https://schema.org/location",
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "privacy": False,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [
                {
                    "id": presence.id,
                    "role": "subject",
                    "person": "/person/the_person/index.json",
                    "event": "/event/the_event/index.json",
                    "privacy": False,
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "date": {
                "start": {
                    "@context": {
                        "iso8601": "https://schema.org/startDate",
                    },
                    "year": 2000,
                    "month": 1,
                    "day": 1,
                    "iso8601": "2000-01-01",
                    "fuzzy": False,
                },
                "end": {
                    "@context": {
                        "iso8601": "https://schema.org/endDate",
                    },
                    "year": 2019,
                    "month": 12,
                    "day": 31,
                    "iso8601": "2019-12-31",
                    "fuzzy": False,
                },
            },
            "place": "/place/the_place/index.json",
            "links": [],
            "name": {DEFAULT_LOCALE_TAG: "The Event"},
            "description": {DEFAULT_LOCALE_TAG: "The Event Description"},
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
            privacy=Privacy.PRIVATE,
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="the_place",
                names=[PlaceName("The Place")],
            ),
        )
        presence = Presence(Person(id="the_person"), Subject(), event)
        event.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "description": "https://schema.org/description",
                "place": "https://schema.org/location",
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "privacy": True,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [
                {
                    "id": presence.id,
                    "person": "/person/the_person/index.json",
                    "event": "/event/the_event/index.json",
                    "privacy": True,
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "place": "/place/the_place/index.json",
            "links": [],
            "fileReferences": [],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected
