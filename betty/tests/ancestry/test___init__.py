from __future__ import annotations

from collections.abc import MutableMapping, Mapping
from pathlib import Path
from typing import Any, Sequence, TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.ancestry import (
    Person,
    Event,
    Presence,
    PersonName,
    Enclosure,
    Source,
    Citation,
    Ancestry,
    FileReference,
)
from betty.ancestry.event_type.event_types import Birth, Unknown as UnknownEventType
from betty.ancestry.file import File
from betty.ancestry.gender.genders import Unknown as UnknownGender, NonBinary
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import Link
from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.ancestry.presence_role.presence_roles import (
    Subject,
    Unknown as UnknownPresenceRole,
)
from betty.ancestry.privacy import Privacy
from betty.date import Date, DateRange
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model.association import OneToOne
from betty.test_utils.ancestry.date import DummyHasDate
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.model import DummyEntity, EntityTestBase

if TYPE_CHECKING:
    from betty.model import Entity
    from betty.serde.dump import Dump, DumpMapping


class DummyHasDateWithContextDefinitions(DummyHasDate):
    @override
    def dated_linked_data_contexts(self) -> tuple[str | None, str | None, str | None]:
        return "single-date", "start-date", "end-date"


class DummyHasFileReferences(HasFileReferences, DummyEntity):
    pass


class TestSource(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Source]:
        return Source

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Source(),
            Source(name="My First Source"),
        ]

    async def test_id(self) -> None:
        source_id = "S1"
        sut = Source(id=source_id)
        assert sut.id == source_id

    async def test_name(self) -> None:
        name = "The Source"
        sut = Source(name=name)
        assert sut.name.localize(DEFAULT_LOCALIZER) == name

    async def test_contained_by(self) -> None:
        contained_by_source = Source()
        sut = Source()
        assert sut.contained_by is None
        sut.contained_by = contained_by_source
        assert sut.contained_by is contained_by_source

    async def test_contains(self) -> None:
        contains_source = Source()
        sut = Source()
        assert list(sut.contains) == []
        sut.contains = [contains_source]
        assert list(sut.contains) == [contains_source]

    async def test_walk_contains_without_contains(self) -> None:
        sut = Source()
        assert list(sut.walk_contains) == []

    async def test_walk_contains_with_contains(self) -> None:
        sut = Source()
        contains = Source(contained_by=sut)
        contains_contains = Source(contained_by=contains)
        assert list(sut.walk_contains) == [contains, contains_contains]

    async def test_citations(self) -> None:
        sut = Source()
        assert list(sut.citations) == []

    async def test_author(self) -> None:
        sut = Source()
        assert not sut.author
        author = "Me"
        sut.author = author
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_publisher(self) -> None:
        sut = Source()
        assert not sut.publisher
        publisher = "Me"
        sut.publisher = publisher
        assert sut.publisher.localize(DEFAULT_LOCALIZER) == publisher

    async def test_date(self) -> None:
        sut = Source()
        assert sut.date is None

    async def test_file_references(self) -> None:
        sut = Source()
        assert list(sut.file_references) == []

    async def test_links(self) -> None:
        sut = Source()
        assert list(sut.links) == []

    async def test_private(self) -> None:
        sut = Source()
        assert sut.privacy is Privacy.UNDETERMINED
        sut.private = True
        assert sut.private is True

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        source = Source(
            id="the_source",
            name="The Source",
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": {"translations": {"und": "The Source"}},
            "contains": [],
            "citations": [],
            "notes": [],
            "links": [
                {
                    "url": "/source/the_source/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/source/the_source/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(source)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        link = Link("https://example.com/the-source")
        link.label = "The Source Online"
        source = Source(
            id="the_source",
            name="The Source",
            author="The Author",
            publisher="The Publisher",
            date=Date(2000, 1, 1),
            contained_by=Source(
                id="the_containing_source",
                name="The Containing Source",
            ),
            contains=[
                Source(
                    id="the_contained_source",
                    name="The Contained Source",
                )
            ],
            links=[link],
        )
        Citation(
            id="the_citation",
            source=source,
        )
        expected: Mapping[str, Any] = {
            "@context": {
                "name": "https://schema.org/name",
            },
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "name": {"translations": {"und": "The Source"}},
            "author": {"translations": {"und": "The Author"}},
            "publisher": {"translations": {"und": "The Publisher"}},
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
            "date": {
                "year": 2000,
                "month": 1,
                "day": 1,
                "iso8601": "2000-01-01",
                "fuzzy": False,
            },
            "links": [
                {
                    "url": "https://example.com/the-source",
                    "label": {
                        "translations": {UNDETERMINED_LOCALE: "The Source Online"}
                    },
                    "locale": "und",
                },
                {
                    "url": "/source/the_source/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/source/the_source/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(source)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        link = Link("https://example.com/the-source")
        link.label = "The Source Online"
        source = Source(
            id="the_source",
            name="The Source",
            author="The Author",
            publisher="The Publisher",
            date=Date(2000, 1, 1),
            contained_by=Source(
                id="the_containing_source",
                name="The Containing Source",
            ),
            contains=[
                Source(
                    id="the_contained_source",
                    name="The Contained Source",
                )
            ],
            links=[link],
            private=True,
        )
        Citation(
            id="the_citation",
            source=source,
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": True,
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
        }
        actual = await assert_dumps_linked_data(source)
        assert isinstance(actual, MutableMapping)
        actual.pop("links")
        assert actual == expected

    async def test_dump_linked_data_should_dump_with_private_associations(self) -> None:
        contained_by_source = Source(
            id="the_containing_source",
            name="The Containing Source",
        )
        contains_source = Source(
            id="the_contained_source",
            name="The Contained Source",
            private=True,
        )
        source = Source(
            id="the_source",
            contained_by=contained_by_source,
            contains=[contains_source],
        )
        Citation(
            id="the_citation",
            source=source,
            private=True,
        )
        expected: Mapping[str, Any] = {
            "@id": "https://example.com/source/the_source/index.json",
            "@type": "https://schema.org/Thing",
            "id": "the_source",
            "private": False,
            "contains": [
                "/source/the_contained_source/index.json",
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "containedBy": "/source/the_containing_source/index.json",
        }
        actual = await assert_dumps_linked_data(source)
        assert isinstance(actual, MutableMapping)
        actual.pop("links")
        assert actual == expected


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


class TestEnclosure(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Enclosure]:
        return Enclosure

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            Enclosure(),
        ]

    async def test_encloses(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert sut.encloses is encloses

    async def test_enclosed_by(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        assert sut.enclosed_by is enclosed_by

    async def test_date(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        date = Date()
        assert sut.date is None
        sut.date = date
        assert sut.date is date

    async def test_citations(self) -> None:
        encloses = Place()
        enclosed_by = Place()
        sut = Enclosure(encloses=encloses, enclosed_by=enclosed_by)
        citation = Citation(source=Source())
        assert sut.date is None
        sut.citations = [citation]
        assert list(sut.citations) == [citation]


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


class TestPersonName(EntityTestBase):
    @override
    def get_sut_class(self) -> type[PersonName]:
        return PersonName

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            PersonName(individual="Jane"),
            PersonName(affiliation="Doe"),
            PersonName(individual="Jane", affiliation="Doe"),
        ]

    async def test_person(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.person == person
        assert [sut] == list(person.names)

    async def test_locale(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert sut.locale is UNDETERMINED_LOCALE

    async def test_citations(self) -> None:
        person = Person(id="1")
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert list(sut.citations) == []

    async def test_individual(self) -> None:
        person = Person(id="1")
        individual = "Janet"
        sut = PersonName(
            person=person,
            individual=individual,
            affiliation="Not a Girl",
        )
        assert sut.individual == individual

    async def test_affiliation(self) -> None:
        person = Person(id="1")
        affiliation = "Not a Girl"
        sut = PersonName(
            person=person,
            individual="Janet",
            affiliation=affiliation,
        )
        assert sut.affiliation == affiliation

    @pytest.mark.parametrize(
        ("expected", "sut"),
        [
            (
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                    },
                    "individual": "Jane",
                    "locale": UNDETERMINED_LOCALE,
                    "private": False,
                    "citations": [],
                },
                PersonName(individual="Jane"),
            ),
            (
                {
                    "@context": {
                        "affiliation": "https://schema.org/familyName",
                    },
                    "affiliation": "Dough",
                    "locale": UNDETERMINED_LOCALE,
                    "private": False,
                    "citations": [],
                },
                PersonName(affiliation="Dough"),
            ),
            (
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                        "affiliation": "https://schema.org/familyName",
                    },
                    "individual": "Jane",
                    "affiliation": "Dough",
                    "locale": "nl-NL",
                    "private": False,
                    "citations": [],
                },
                PersonName(individual="Jane", affiliation="Dough", locale="nl-NL"),
            ),
            (
                {
                    "locale": "nl-NL",
                    "private": True,
                    "citations": [],
                },
                PersonName(
                    individual="Jane", affiliation="Dough", locale="nl-NL", private=True
                ),
            ),
        ],
    )
    async def test_dump_linked_data(
        self, expected: DumpMapping[Dump], sut: PersonName
    ) -> None:
        assert await assert_dumps_linked_data(sut) == expected


class TestPerson(EntityTestBase):
    @override
    def get_sut_class(self) -> type[Person]:
        return Person

    @override
    async def get_sut_instances(self) -> Sequence[Entity]:
        return [
            # No names.
            Person(),
            # No public names.
            Person(
                names=[PersonName(individual="Jane", affiliation="Doe", private=True)]
            ),
            # One public name.
            Person(names=[PersonName(individual="Jane", affiliation="Doe")]),
        ]

    async def test_parents(self) -> None:
        sut = Person(id="1")
        parent = Person(id="2")
        sut.parents.add(parent)
        assert list(sut.parents) == [parent]
        assert [sut] == list(parent.children)
        sut.parents.remove(parent)
        assert list(sut.parents) == []
        assert list(parent.children) == []

    async def test_children(self) -> None:
        sut = Person(id="1")
        child = Person(id="2")
        sut.children.add(child)
        assert list(sut.children) == [child]
        assert [sut] == list(child.parents)
        sut.children.remove(child)
        assert list(sut.children) == []
        assert list(child.parents) == []

    async def test_presences(self) -> None:
        event = Event(event_type=Birth())
        sut = Person(id="1")
        presence = Presence(sut, Subject(), event)
        sut.presences.add(presence)
        assert list(sut.presences) == [presence]
        assert sut == presence.person
        sut.presences.remove(presence)
        assert list(sut.presences) == []
        assert presence.person is None

    async def test_names(self) -> None:
        sut = Person(id="1")
        name = PersonName(
            person=sut,
            individual="Janet",
            affiliation="Not a Girl",
        )
        assert list(sut.names) == [name]
        assert sut == name.person
        sut.names.remove(name)
        assert list(sut.names) == []
        assert name.person is None

    async def test_id(self) -> None:
        person_id = "P1"
        sut = Person(id=person_id)
        assert sut.id == person_id

    async def test_file_references(self) -> None:
        sut = Person(id="1")
        assert list(sut.file_references) == []

    async def test_citations(self) -> None:
        sut = Person(id="1")
        assert list(sut.citations) == []

    async def test_links(self) -> None:
        sut = Person(id="1")
        assert list(sut.links) == []

    async def test_private(self) -> None:
        sut = Person(id="1")
        assert sut.privacy is Privacy.UNDETERMINED

    async def test_siblings_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.siblings) == []

    async def test_siblings_with_one_common_parent(self) -> None:
        sut = Person(id="1")
        sibling = Person(id="2")
        parent = Person(id="3")
        parent.children = [sut, sibling]
        assert list(sut.siblings) == [sibling]

    async def test_siblings_with_multiple_common_parents(self) -> None:
        sut = Person(id="1")
        sibling = Person(id="2")
        parent = Person(id="3")
        parent.children = [sut, sibling]
        assert list(sut.siblings) == [sibling]

    async def test_ancestors_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.ancestors) == []

    async def test_ancestors_with_parent(self) -> None:
        sut = Person(id="1")
        parent = Person(id="3")
        sut.parents.add(parent)
        grandparent = Person(id="2")
        parent.parents.add(grandparent)
        assert list(sut.ancestors) == [parent, grandparent]

    async def test_descendants_without_parents(self) -> None:
        sut = Person(id="person")
        assert list(sut.descendants) == []

    async def test_descendants_with_parent(self) -> None:
        sut = Person(id="1")
        child = Person(id="3")
        sut.children.add(child)
        grandchild = Person(id="2")
        child.children.add(grandchild)
        assert list(sut.descendants) == [child, grandchild]

    async def test_dump_linked_data_should_dump_minimal(self) -> None:
        person_id = "the_person"
        person = Person(id=person_id)
        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "private": False,
            "gender": UnknownGender.plugin_id(),
            "names": [],
            "parents": [],
            "children": [],
            "siblings": [],
            "presences": [],
            "citations": [],
            "notes": [],
            "links": [
                {
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    async def test_dump_linked_data_should_dump_full(self) -> None:
        parent_id = "the_parent"
        parent = Person(id=parent_id)

        child_id = "the_child"
        child = Person(id=child_id)

        sibling_id = "the_sibling"
        sibling = Person(id=sibling_id)
        sibling.parents.add(parent)

        person_id = "the_person"
        person_affiliation_name = "Person"
        person_individual_name = "The"
        person = Person(id=person_id, public=True, gender=NonBinary())
        PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
            locale="en-US",
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link(
            "https://example.com/the-person",
            label="The Person Online",
        )
        person.links.append(link)
        person.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        Presence(
            person,
            Subject(),
            Event(
                id="the_event",
                event_type=Birth(),
            ),
        )

        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "private": False,
            "gender": NonBinary.plugin_id(),
            "names": [
                {
                    "@context": {
                        "individual": "https://schema.org/givenName",
                        "affiliation": "https://schema.org/familyName",
                    },
                    "individual": person_individual_name,
                    "affiliation": person_affiliation_name,
                    "locale": "en-US",
                    "citations": [],
                    "private": False,
                },
            ],
            "parents": [
                "/person/the_parent/index.json",
            ],
            "children": [
                "/person/the_child/index.json",
            ],
            "siblings": [
                "/person/the_sibling/index.json",
            ],
            "presences": [
                {
                    "@context": {
                        "event": "https://schema.org/performerIn",
                    },
                    "role": "subject",
                    "event": "/event/the_event/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "url": "https://example.com/the-person",
                    "label": {
                        "translations": {UNDETERMINED_LOCALE: "The Person Online"}
                    },
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
                {
                    "url": "/person/the_person/index.html",
                    "relationship": "alternate",
                    "mediaType": "text/html",
                    "locale": "en-US",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
        assert actual == expected

    async def test_dump_linked_data_should_dump_private(self) -> None:
        parent_id = "the_parent"
        parent = Person(id=parent_id)

        child_id = "the_child"
        child = Person(id=child_id)

        sibling_id = "the_sibling"
        sibling = Person(id=sibling_id)
        sibling.parents.add(parent)

        person_id = "the_person"
        person_affiliation_name = "Person"
        person_individual_name = "The"
        person = Person(
            id=person_id,
            private=True,
        )
        PersonName(
            person=person,
            individual=person_individual_name,
            affiliation=person_affiliation_name,
        )
        person.parents.add(parent)
        person.children.add(child)
        link = Link("https://example.com/the-person")
        link.label = "The Person Online"
        person.links.append(link)
        person.citations.add(
            Citation(
                id="the_citation",
                source=Source(
                    id="the_source",
                    name="The Source",
                ),
            )
        )
        Presence(
            person,
            Subject(),
            Event(
                id="the_event",
                event_type=Birth(),
            ),
        )

        expected: Mapping[str, Any] = {
            "@context": {
                "names": "https://schema.org/name",
                "parents": "https://schema.org/parent",
                "children": "https://schema.org/child",
                "siblings": "https://schema.org/sibling",
            },
            "@id": "https://example.com/person/the_person/index.json",
            "@type": "https://schema.org/Person",
            "id": person_id,
            "names": [],
            "parents": [
                "/person/the_parent/index.json",
            ],
            "children": [
                "/person/the_child/index.json",
            ],
            "siblings": [
                "/person/the_sibling/index.json",
            ],
            "private": True,
            "presences": [
                {
                    "@context": {
                        "event": "https://schema.org/performerIn",
                    },
                    "event": "/event/the_event/index.json",
                },
            ],
            "citations": [
                "/citation/the_citation/index.json",
            ],
            "notes": [],
            "links": [
                {
                    "url": "/person/the_person/index.json",
                    "relationship": "canonical",
                    "mediaType": "application/ld+json",
                    "locale": "und",
                },
            ],
        }
        actual = await assert_dumps_linked_data(person)
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


class TestFileReference:
    async def test_focus(self) -> None:
        sut = FileReference()
        focus = (1, 2, 3, 4)
        sut.focus = focus
        assert sut.focus == focus

    async def test_file(self) -> None:
        file = File(Path())
        sut = FileReference(None, file)
        assert sut.file is file

    async def test_referee(self) -> None:
        referee = DummyHasFileReferences()
        sut = FileReference(referee)
        assert sut.referee is referee
