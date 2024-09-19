from __future__ import annotations

from typing import Any, Sequence, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry import Event, Presence, Citation, Ancestry
from betty.ancestry.event_type.event_types import Birth, Unknown as UnknownEventType
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.name import Name
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence_role.presence_roles import (
    Subject,
    Unknown as UnknownPresenceRole,
)
from betty.ancestry.privacy import Privacy
from betty.ancestry.source import Source
from betty.date import Date, DateRange
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model.association import OneToOne
from betty.test_utils.ancestry.date import DummyHasDate
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import DummyEntity, EntityTestBase

if TYPE_CHECKING:
    from collections.abc import Mapping
    from betty.model import Entity


class DummyHasDateWithContextDefinitions(DummyHasDate):
    @override
    def dated_linked_data_contexts(self) -> tuple[str | None, str | None, str | None]:
        return "single-date", "start-date", "end-date"


class DummyHasFileReferences(HasFileReferences, DummyEntity):
    pass


class DummyHasCitations(HasCitations, DummyEntity):
    pass


class TestCitation(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Citation]:
        return Citation

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Citation(),
            Citation(location="My First Location"),
        ]

    async def test_id(self) -> None:
        citation_id = "C1"
        sut = Citation(
            id=citation_id,
            source=Source(),
        )
        assert sut.id == citation_id

    async def test_facts(self) -> None:
        fact = DummyHasCitations()
        sut = Citation(source=Source())
        assert list(sut.facts) == []
        sut.facts = [fact]
        assert list(sut.facts) == [fact]

    async def test_source(self) -> None:
        source = Source()
        sut = Citation(source=source)
        assert sut.source is source

    async def test_location(self) -> None:
        sut = Citation(source=Source())
        assert not sut.location
        location = "Somewhere"
        sut.location = location
        assert sut.location.localize(DEFAULT_LOCALIZER) == location

    async def test_date(self) -> None:
        sut = Citation(source=Source())
        assert sut.date is None

    async def test_file_references(self) -> None:
        sut = Citation(source=Source())
        assert list(sut.file_references) == []

    async def test_private(self) -> None:
        sut = Citation(source=Source())
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(name="The Source"),
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": False,
            "facts": [],
            "links": [
                {
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/citation/the_citation/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(
                id="the_source",
                name="The Source",
            ),
        )
        citation.facts.add(
            Event(
                id="the_event",
                event_type=Birth(),
            )
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": False,
            "source": "/source/the_source/index.json",
            "facts": ["/event/the_event/index.json"],
            "links": [
                {
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/citation/the_citation/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        citation = Citation(
            id="the_citation",
            source=Source(
                id="the_source",
                name="The Source",
            ),
            private=True,
        )
        citation.facts.add(
            Event(
                id="the_event",
                event_type=Birth(),
            )
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/citation/the_citation/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_citation",
            "private": True,
            "source": "/source/the_source/index.json",
            "facts": ["/event/the_event/index.json"],
            "links": [
                {
                    "url": "/citation/the_citation/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
            ],
        }
        actual = await assert_dumps_linked_data(citation)
        assert actual == expected


class TestPresence(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Presence]:
        return Presence

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Presence(None, UnknownPresenceRole(), None),
            Presence(Person(), UnknownPresenceRole(), None),
            Presence(None, UnknownPresenceRole(), Event()),
            Presence(Person(), UnknownPresenceRole(), Event()),
        ]

    async def test_person(self) -> None:
        person = Person()
        sut = Presence(person, Subject(), Event(event_type=UnknownEventType()))
        assert sut.person == person

    async def test_event(self) -> None:
        role = Subject()
        sut = Presence(Person(), role, Event(event_type=UnknownEventType()))
        assert sut.role == role

    async def test_role(self) -> None:
        event = Event(event_type=UnknownEventType())
        sut = Presence(Person(), Subject(), event)
        assert sut.event == event

    @pytest.mark.parametrize(
        ("expected", "person_privacy", "presence_privacy", "event_privacy"),
        [
            (Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PUBLIC),
            (Privacy.PRIVATE, Privacy.PRIVATE, Privacy.PUBLIC, Privacy.PUBLIC),
            (Privacy.PRIVATE, Privacy.PUBLIC, Privacy.PUBLIC, Privacy.PRIVATE),
        ],
    )
    async def test_privacy(
        self,
        expected: Privacy,
        person_privacy: Privacy,
        presence_privacy: Privacy,
        event_privacy: Privacy,
    ) -> None:
        person = Person(privacy=person_privacy)
        event = Event(privacy=event_privacy, event_type=UnknownEventType())
        sut = Presence(person, Subject(), event)
        sut.privacy = presence_privacy

        assert sut.privacy == expected


class TestEvent(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Event]:
        return Event

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Event(),
            Event(description="My First Event"),
        ]

    async def test_id(self) -> None:
        event_id = "E1"
        sut = Event(
            id=event_id,
            event_type=UnknownEventType(),
        )
        assert sut.id == event_id

    async def test_place(self) -> None:
        place = Place(
            id="1",
            names=[Name("one")],
        )
        sut = Event(event_type=UnknownEventType())
        sut.place = place
        assert sut.place == place
        assert sut in place.events
        sut.place = None
        assert sut.place is None
        assert sut not in place.events

    async def test_presences(self) -> None:
        person = Person(id="P1")
        sut = Event(event_type=UnknownEventType())
        presence = Presence(person, Subject(), sut)
        sut.presences.add(presence)
        assert list(sut.presences) == [presence]
        assert sut == presence.event
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        assert presence.event is None

    async def test_date(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert sut.date is None
        date = Date()
        sut.date = date
        assert sut.date == date

    async def test_file_references(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert list(sut.file_references) == []

    async def test_citations(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert list(sut.citations) == []

    async def test_description(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert not sut.description

    async def test_private(self) -> None:
        sut = Event(event_type=UnknownEventType())
        assert sut.privacy is Privacy.UNDETERMINED

    async def test_event_type(self) -> None:
        event_type = UnknownEventType()
        sut = Event(event_type=event_type)
        assert sut.event_type is event_type

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "private": False,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [
                {
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/event/the_event/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="the_place",
                names=[Name("The Place")],
            ),
        )
        Presence(Person(id="the_person"), Subject(), event)
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
                "place": "https://schema.org/location",
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "private": False,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [
                {
                    "@type": "https://schema.org/Person",
                    "role": "subject",
                    "person": "/person/the_person/index.json",
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
            "links": [
                {
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/event/the_event/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        event = Event(
            id="the_event",
            event_type=Birth(),
            private=True,
            date=DateRange(Date(2000, 1, 1), Date(2019, 12, 31)),
            place=Place(
                id="the_place",
                names=[Name("The Place")],
            ),
        )
        Presence(Person(id="the_person"), Subject(), event)
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
                "place": "https://schema.org/location",
                "presences": "https://schema.org/performer",
            },
            "@id": "https://example.com/event/the_event/index.json",
            "@type": "https://schema.org/Event",
            "id": "the_event",
            "private": True,
            "type": "birth",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "eventStatus": "https://schema.org/EventScheduled",
            "presences": [
                {
                    "@type": "https://schema.org/Person",
                    "person": "/person/the_person/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "place": "/place/the_place/index.json",
            "links": [
                {
                    "url": "/event/the_event/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
            ],
        }
        actual = await assert_dumps_linked_data(event)
        assert actual == expected


class _TestAncestry_OneToOne_Left(DummyEntity):
    one_right = OneToOne["_TestAncestry_OneToOne_Left", "_TestAncestry_OneToOne_Right"](
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Left",
        "one_right",
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Right",
        "one_left",
    )


class _TestAncestry_OneToOne_Right(DummyEntity):
    one_left = OneToOne["_TestAncestry_OneToOne_Right", _TestAncestry_OneToOne_Left](
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Right",
        "one_left",
        "betty.tests.ancestry.test___init__:_TestAncestry_OneToOne_Left",
        "one_right",
    )


class TestAncestry:
    async def test_add_(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        sut.add(left)
        assert left in sut
        assert right in sut

    async def test_add_unchecked_graph(self) -> None:
        sut = Ancestry()
        left = _TestAncestry_OneToOne_Left()
        right = _TestAncestry_OneToOne_Right()
        left.one_right = right
        sut.add_unchecked_graph(left)
        assert left in sut
        assert right not in sut
