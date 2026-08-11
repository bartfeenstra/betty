from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from betty.associations.to_one import MissingAssociate, Placeholder
from betty.date import Date, DateRange
from betty.entities.citation import Citation
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.place_name import PlaceName
from betty.entities.presence import Presence
from betty.entities.source import Source
from betty.entity import Entity
from betty.event_types.birth import Birth
from betty.event_types.unknown import UnknownEventType
from betty.locale import default_locale_tag
from betty.localizer import default_localizer
from betty.privacy import Privacy
from betty.roles.subject import Subject
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

    async def test_dump_linked_data__should_dump_minimal(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        event = Event(
            id="my-first-event",
            event_type=Birth(),
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "description": "https://schema.org/description",
                "place": "https://schema.org/location",
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/my-first-event/index.json",
            "@type": "https://schema.org/Event",
            "id": "my-first-event",
            "privacy": False,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [],
            "files": [],
            "place": None,
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected

    async def test_dump_linked_data__should_dump_full(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        event = Event(
            id="my-first-event",
            event_type=Birth(),
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="my-first-place",
                names=[PlaceName("The Place")],
            ),
            name="The Event",
            description="The Event Description",
        )
        Presence(Person(id="my-first-person"), Subject(), event, id="my-first-presence")
        event.citations.add(
            Citation(
                id="my-first-citation",
                source=Source(
                    id="my-first-source",
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
            "@id": "https://example.com/event/my-first-event/index.json",
            "@type": "https://schema.org/Event",
            "id": "my-first-event",
            "privacy": False,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [
                "/presence/my-first-presence/index.json",
            ],
            "citations": [
                "/citation/my-first-citation/index.json",
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
            "place": "/place/my-first-place/index.json",
            "links": [],
            "name": {default_locale_tag: "The Event"},
            "description": {default_locale_tag: "The Event Description"},
            "files": [],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected

    async def test_dump_linked_data__should_dump_private(
        self, assert_dumps_linked_data: AssertDumpsLinkedData
    ) -> None:
        event = Event(
            id="my-first-event",
            event_type=Birth(),
            privacy=Privacy.PRIVATE,
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="my-first-place",
                names=[PlaceName("The Place")],
            ),
        )
        Presence(Person(id="my-first-person"), Subject(), event, id="my-first-presence")
        event.citations.add(
            Citation(
                id="my-first-citation",
                source=Source(
                    id="my-first-source",
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
            "@id": "https://example.com/event/my-first-event/index.json",
            "@type": "https://schema.org/Event",
            "id": "my-first-event",
            "privacy": True,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [
                "/presence/my-first-presence/index.json",
            ],
            "citations": [
                "/citation/my-first-citation/index.json",
            ],
            "notes": [],
            "place": "/place/my-first-place/index.json",
            "links": [],
            "files": [],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected
