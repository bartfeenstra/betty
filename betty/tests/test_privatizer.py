from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from betty.locale import Date, DateRange
from betty.model.ancestry import Person, Presence, Event, Source, File, Subject, Attendee, Citation, Privacy
from betty.model.event_type import Death, Birth, Marriage
from betty.privatizer import Privatizer
from betty.project import DEFAULT_LIFETIME_THRESHOLD


def _expand_person(generation: int) -> list[tuple[bool, Privacy, Event | None]]:
    multiplier = abs(generation) + 1 if generation < 0 else 1
    lifetime_threshold_year = datetime.now().year - DEFAULT_LIFETIME_THRESHOLD * multiplier
    date_underDEFAULT_LIFETIME_THRESHOLD = Date(lifetime_threshold_year + 1, 1, 1)
    date_range_start_underDEFAULT_LIFETIME_THRESHOLD = DateRange(date_underDEFAULT_LIFETIME_THRESHOLD)
    date_range_end_underDEFAULT_LIFETIME_THRESHOLD = DateRange(None, date_underDEFAULT_LIFETIME_THRESHOLD)
    date_overDEFAULT_LIFETIME_THRESHOLD = Date(lifetime_threshold_year - 1, 1, 1)
    date_range_start_overDEFAULT_LIFETIME_THRESHOLD = DateRange(date_overDEFAULT_LIFETIME_THRESHOLD)
    date_range_end_overDEFAULT_LIFETIME_THRESHOLD = DateRange(None, date_overDEFAULT_LIFETIME_THRESHOLD)
    return [
        # If there are no events for a person, they are private.
        (True, Privacy.UNDETERMINED, None),
        (True, Privacy.PRIVATE, None),
        (False, Privacy.PUBLIC, None),

        # Deaths and other end-of-life events are special, but only for the person whose privacy is being checked:
        # - If they're present without dates, the person isn't private.
        # - If they're present and their dates or date ranges' end dates are in the past, the person isn't private.
        (generation != 0, Privacy.UNDETERMINED, Event(
            event_type=Death,
            date=Date(datetime.now().year, datetime.now().month, datetime.now().day),
        )),
        (generation != 0, Privacy.UNDETERMINED, Event(
            event_type=Death,
            date=date_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.UNDETERMINED, Event(
            event_type=Death,
            date=date_range_start_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (generation != 0, Privacy.UNDETERMINED, Event(
            event_type=Death,
            date=date_range_end_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.UNDETERMINED, Event(
            event_type=Death,
            date=date_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.UNDETERMINED, Event(
            event_type=Death,
            date=date_range_start_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.UNDETERMINED, Event(
            event_type=Death,
            date=date_range_end_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.PRIVATE, Event(event_type=Death)),
        (False, Privacy.PUBLIC, Event(event_type=Death)),
        (generation != 0, Privacy.UNDETERMINED, Event(event_type=Death)),

        # Regular events without dates do not affect privacy.
        (True, Privacy.UNDETERMINED, Event(event_type=Birth)),
        (True, Privacy.PRIVATE, Event(event_type=Birth)),
        (False, Privacy.PUBLIC, Event(event_type=Birth)),

        # Regular events with incomplete dates do not affect privacy.
        (True, Privacy.UNDETERMINED, Event(
            event_type=Birth,
            date=Date(),
        )),
        (True, Privacy.PRIVATE, Event(
            event_type=Birth,
            date=Date(),
        )),
        (False, Privacy.PUBLIC, Event(
            event_type=Birth,
            date=Date(),
        )),

        # Regular events under the lifetime threshold do not affect privacy.
        (True, Privacy.UNDETERMINED, Event(
            event_type=Birth,
            date=date_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.PRIVATE, Event(
            event_type=Birth,
            date=date_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.PUBLIC, Event(
            event_type=Birth,
            date=date_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.UNDETERMINED, Event(
            event_type=Birth,
            date=date_range_start_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.PRIVATE, Event(
            event_type=Birth,
            date=date_range_start_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.PUBLIC, Event(
            event_type=Birth,
            date=date_range_start_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.UNDETERMINED, Event(
            event_type=Birth,
            date=date_range_end_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.PRIVATE, Event(
            event_type=Birth,
            date=date_range_end_underDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.PUBLIC, Event(
            event_type=Birth,
            date=date_range_end_underDEFAULT_LIFETIME_THRESHOLD,
        )),

        # Regular events over the lifetime threshold affect privacy.
        (False, Privacy.UNDETERMINED, Event(
            event_type=Birth,
            date=date_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.PRIVATE, Event(
            event_type=Birth,
            date=date_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.PUBLIC, Event(
            event_type=Birth,
            date=date_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.UNDETERMINED, Event(
            event_type=Birth,
            date=date_range_start_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.PRIVATE, Event(
            event_type=Birth,
            date=date_range_start_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.PUBLIC, Event(
            event_type=Birth,
            date=date_range_start_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.UNDETERMINED, Event(
            event_type=Birth,
            date=date_range_end_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (True, Privacy.PRIVATE, Event(
            event_type=Birth,
            date=date_range_end_overDEFAULT_LIFETIME_THRESHOLD,
        )),
        (False, Privacy.PUBLIC, Event(
            event_type=Birth,
            date=date_range_end_overDEFAULT_LIFETIME_THRESHOLD,
        )),
    ]


class TestPrivatizer:
    async def test_privatize_person_should_not_privatize_if_public(self) -> None:
        source_file = File(
            id='F0',
            path=Path(__file__),
        )
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File(
            id='F1',
            path=Path(__file__),
        )
        citation = Citation(
            id='C0',
            source=source,
        )
        citation.files.add(citation_file)
        event_as_subject = Event(event_type=Birth)
        event_as_attendee = Event(event_type=Marriage)
        person_file = File(
            id='F2',
            path=Path(__file__),
        )
        person = Person(
            id='P0',
            public=True,
        )
        person.citations.add(citation)
        person.files.add(person_file)
        Presence(person, Subject(), event_as_subject)
        Presence(person, Attendee(), event_as_attendee)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert not person.private
        assert citation.privacy is Privacy.UNDETERMINED
        assert source.privacy is Privacy.UNDETERMINED
        assert person_file.privacy is Privacy.UNDETERMINED
        assert citation_file.privacy is Privacy.UNDETERMINED
        assert source_file.privacy is Privacy.UNDETERMINED
        assert event_as_subject.privacy is Privacy.UNDETERMINED
        assert event_as_attendee.privacy is Privacy.UNDETERMINED

    async def test_privatize_person_should_privatize_if_private(self) -> None:
        source_file = File(
            id='F0',
            path=Path(__file__),
        )
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File(
            id='F1',
            path=Path(__file__),
        )
        citation = Citation(
            id='C0',
            source=source,
        )
        citation.files.add(citation_file)
        event_as_subject = Event(event_type=Birth)
        event_as_attendee = Event(event_type=Marriage)
        person_file = File(
            id='F2',
            path=Path(__file__),
        )
        person = Person(
            id='P0',
            private=True,
        )
        person.citations.add(citation)
        person.files.add(person_file)
        Presence(person, Subject(), event_as_subject)
        Presence(person, Attendee(), event_as_attendee)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert person.private
        assert citation.private
        assert source.private
        assert person_file.private
        assert citation_file.private
        assert source_file.private
        assert event_as_subject.private
        assert event_as_attendee.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(0))
    async def test_privatize_person_without_relatives(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(
            id='P0',
            privacy=privacy,
        )
        if event is not None:
            Presence(person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(1))
    async def test_privatize_person_with_child(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(
            id='P0',
            privacy=privacy,
        )
        child = Person(id='P1')
        if event is not None:
            Presence(child, Subject(), event)
        person.children.add(child)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(2))
    async def test_privatize_person_with_grandchild(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(
            id='P0',
            privacy=privacy,
        )
        child = Person(id='P1')
        person.children.add(child)
        grandchild = Person(id='P2')
        if event is not None:
            Presence(grandchild, Subject(), event)
        child.children.add(grandchild)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(3))
    async def test_privatize_person_with_great_grandchild(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(
            id='P0',
            privacy=privacy,
        )
        child = Person(id='P1')
        person.children.add(child)
        grandchild = Person(id='P2')
        child.children.add(grandchild)
        great_grandchild = Person(id='P2')
        if event is not None:
            Presence(great_grandchild, Subject(), event)
        grandchild.children.add(great_grandchild)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(-1))
    async def test_privatize_person_with_parent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(
            id='P0',
            privacy=privacy,
        )
        parent = Person(id='P1')
        if event is not None:
            Presence(parent, Subject(), event)
        person.parents.add(parent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(-2))
    async def test_privatize_person_with_grandparent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(
            id='P0',
            privacy=privacy,
        )
        parent = Person(id='P1')
        person.parents.add(parent)
        grandparent = Person(id='P2')
        if event is not None:
            Presence(grandparent, Subject(), event)
        parent.parents.add(grandparent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(-3))
    async def test_privatize_person_with_great_grandparent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person(
            id='P0',
            privacy=privacy,
        )
        parent = Person(id='P1')
        person.parents.add(parent)
        grandparent = Person(id='P2')
        parent.parents.add(grandparent)
        great_grandparent = Person(id='P2')
        if event is not None:
            Presence(great_grandparent, Subject(), event)
        grandparent.parents.add(great_grandparent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    async def test_privatize_event_should_not_privatize_if_public(self) -> None:
        source_file = File(
            id='F0',
            path=Path(__file__),
        )
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File(
            id='F1',
            path=Path(__file__),
        )
        citation = Citation(
            id='C0',
            source=source,
        )
        citation.files.add(citation_file)
        event_file = File(
            id='F1',
            path=Path(__file__),
        )
        event = Event(
            id='E1',
            event_type=Birth,
            public=True,
        )
        event.citations.add(citation)
        event.files.add(event_file)
        person = Person(id='P0')
        Presence(person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(event)
        assert not event.private
        assert event_file.privacy is Privacy.UNDETERMINED
        assert citation.privacy is Privacy.UNDETERMINED
        assert source.privacy is Privacy.UNDETERMINED
        assert citation_file.privacy is Privacy.UNDETERMINED
        assert source_file.privacy is Privacy.UNDETERMINED
        assert person.privacy is Privacy.UNDETERMINED

    async def test_privatize_event_should_privatize_if_private(self) -> None:
        source_file = File(
            id='F0',
            path=Path(__file__),
        )
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File(
            id='F1',
            path=Path(__file__),
        )
        citation = Citation(
            id='C0',
            source=source,
        )
        citation.files.add(citation_file)
        event_file = File(
            id='F1',
            path=Path(__file__),
        )
        event = Event(
            id='E1',
            event_type=Birth,
            private=True,
        )
        event.citations.add(citation)
        event.files.add(event_file)
        person = Person(id='P0')
        Presence(person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(event)
        assert event.private
        assert event_file.private
        assert citation.private
        assert source.private
        assert citation_file.private
        assert source_file.private
        assert person.privacy is Privacy.UNDETERMINED

    async def test_privatize_source_should_not_privatize_if_public(self) -> None:
        file = File(
            id='F0',
            path=Path(__file__),
        )
        source = Source(
            id='S0',
            name='The Source',
            public=True,
        )
        source.files.add(file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(source)
        assert not source.private
        assert file.privacy is Privacy.UNDETERMINED

    async def test_privatize_source_should_privatize_if_private(self) -> None:
        file = File(
            id='F0',
            path=Path(__file__),
        )
        source = Source(
            id='S0',
            name='The Source',
            private=True,
        )
        source.files.add(file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(source)
        assert source.private
        assert file.private

    async def test_privatize_citation_should_not_privatize_if_public(self) -> None:
        source_file = File(
            id='F0',
            path=Path(__file__),
        )
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File(
            id='F1',
            path=Path(__file__),
        )
        citation = Citation(
            id='C0',
            source=source,
            public=True,
        )
        citation.files.add(citation_file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(citation)
        assert not citation.private
        assert source.privacy is Privacy.UNDETERMINED
        assert citation_file.privacy is Privacy.UNDETERMINED
        assert source_file.privacy is Privacy.UNDETERMINED

    async def test_privatize_citation_should_privatize_if_private(self) -> None:
        source_file = File(
            id='F0',
            path=Path(__file__),
        )
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File(
            id='F1',
            path=Path(__file__),
        )
        citation = Citation(
            id='C0',
            source=source,
            private=True,
        )
        citation.files.add(citation_file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(citation)
        assert citation.private
        assert source.private
        assert citation_file.private
        assert source_file.private

    async def test_privatize_file_should_not_privatize_if_public(self) -> None:
        source = Source(name='The Source')
        citation = Citation(source=source)
        file = File(
            id='F0',
            path=Path(__file__),
            public=True,
        )
        file.citations.add(citation)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(file)
        assert not file.private
        assert citation.privacy is Privacy.UNDETERMINED

    async def test_privatize_file_should_privatize_if_private(self) -> None:
        source = Source(name='The Source')
        citation = Citation(source=source)
        file = File(
            id='F0',
            path=Path(__file__),
            private=True,
        )
        file.citations.add(citation)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(file)
        assert file.private
        assert citation.private
