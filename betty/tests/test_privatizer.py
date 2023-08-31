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
        (generation != 0, Privacy.UNDETERMINED, Event(None, Death, date=Date(datetime.now().year, datetime.now().month, datetime.now().day))),
        (generation != 0, Privacy.UNDETERMINED, Event(None, Death, date=date_underDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.UNDETERMINED, Event(None, Death, date=date_range_start_underDEFAULT_LIFETIME_THRESHOLD)),
        (generation != 0, Privacy.UNDETERMINED, Event(None, Death, date=date_range_end_underDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.UNDETERMINED, Event(None, Death, date=date_overDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.UNDETERMINED, Event(None, Death, date=date_range_start_overDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.UNDETERMINED, Event(None, Death, date=date_range_end_overDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.PRIVATE, Event(None, Death)),
        (False, Privacy.PUBLIC, Event(None, Death)),
        (generation != 0, Privacy.UNDETERMINED, Event(None, Death)),

        # Regular events without dates do not affect privacy.
        (True, Privacy.UNDETERMINED, Event(None, Birth)),
        (True, Privacy.PRIVATE, Event(None, Birth)),
        (False, Privacy.PUBLIC, Event(None, Birth)),

        # Regular events with incomplete dates do not affect privacy.
        (True, Privacy.UNDETERMINED, Event(None, Birth, date=Date())),
        (True, Privacy.PRIVATE, Event(None, Birth, date=Date())),
        (False, Privacy.PUBLIC, Event(None, Birth, date=Date())),

        # Regular events under the lifetime threshold do not affect privacy.
        (True, Privacy.UNDETERMINED, Event(None, Birth, date=date_underDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.PRIVATE, Event(None, Birth, date=date_underDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.PUBLIC, Event(None, Birth, date=date_underDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.UNDETERMINED, Event(None, Birth, date=date_range_start_underDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.PRIVATE, Event(None, Birth, date=date_range_start_underDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.PUBLIC, Event(None, Birth, date=date_range_start_underDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.UNDETERMINED, Event(None, Birth, date=date_range_end_underDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.PRIVATE, Event(None, Birth, date=date_range_end_underDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.PUBLIC, Event(None, Birth, date=date_range_end_underDEFAULT_LIFETIME_THRESHOLD)),

        # Regular events over the lifetime threshold affect privacy.
        (False, Privacy.UNDETERMINED, Event(None, Birth, date=date_overDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.PRIVATE, Event(None, Birth, date=date_overDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.PUBLIC, Event(None, Birth, date=date_overDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.UNDETERMINED, Event(None, Birth, date=date_range_start_overDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.PRIVATE, Event(None, Birth, date=date_range_start_overDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.PUBLIC, Event(None, Birth, date=date_range_start_overDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.UNDETERMINED, Event(None, Birth, date=date_range_end_overDEFAULT_LIFETIME_THRESHOLD)),
        (True, Privacy.PRIVATE, Event(None, Birth, date=date_range_end_overDEFAULT_LIFETIME_THRESHOLD)),
        (False, Privacy.PUBLIC, Event(None, Birth, date=date_range_end_overDEFAULT_LIFETIME_THRESHOLD)),
    ]


class TestPrivatizer:
    def test_privatize_person_should_not_privatize_if_public(self) -> None:
        source_file = File('F0', Path(__file__))
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File('F1', Path(__file__))
        citation = Citation('C0', source)
        citation.files.add(citation_file)
        event_as_subject = Event(None, Birth)
        event_as_attendee = Event(None, Marriage)
        person_file = File('F2', Path(__file__))
        person = Person('P0')
        person.public = True
        person.citations.add(citation)
        person.files.add(person_file)
        Presence(None, person, Subject(), event_as_subject)
        Presence(None, person, Attendee(), event_as_attendee)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert not person.private
        assert citation.privacy is Privacy.UNDETERMINED
        assert source.privacy is Privacy.UNDETERMINED
        assert person_file.privacy is Privacy.UNDETERMINED
        assert citation_file.privacy is Privacy.UNDETERMINED
        assert source_file.privacy is Privacy.UNDETERMINED
        assert event_as_subject.privacy is Privacy.UNDETERMINED
        assert event_as_attendee.privacy is Privacy.UNDETERMINED

    def test_privatize_person_should_privatize_if_private(self) -> None:
        source_file = File('F0', Path(__file__))
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File('F1', Path(__file__))
        citation = Citation('C0', source)
        citation.files.add(citation_file)
        event_as_subject = Event(None, Birth)
        event_as_attendee = Event(None, Marriage)
        person_file = File('F2', Path(__file__))
        person = Person('P0')
        person.private = True
        person.citations.add(citation)
        person.files.add(person_file)
        Presence(None, person, Subject(), event_as_subject)
        Presence(None, person, Attendee(), event_as_attendee)
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
    def test_privatize_person_without_relatives(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person('P0')
        person.privacy = privacy
        if event is not None:
            Presence(None, person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(1))
    def test_privatize_person_with_child(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person('P0')
        person.privacy = privacy
        child = Person('P1')
        if event is not None:
            Presence(None, child, Subject(), event)
        person.children.add(child)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(2))
    def test_privatize_person_with_grandchild(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person('P0')
        person.privacy = privacy
        child = Person('P1')
        person.children.add(child)
        grandchild = Person('P2')
        if event is not None:
            Presence(None, grandchild, Subject(), event)
        child.children.add(grandchild)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(3))
    def test_privatize_person_with_great_grandchild(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person('P0')
        person.privacy = privacy
        child = Person('P1')
        person.children.add(child)
        grandchild = Person('P2')
        child.children.add(grandchild)
        great_grandchild = Person('P2')
        if event is not None:
            Presence(None, great_grandchild, Subject(), event)
        grandchild.children.add(great_grandchild)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(-1))
    def test_privatize_person_with_parent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person('P0')
        person.privacy = privacy
        parent = Person('P1')
        if event is not None:
            Presence(None, parent, Subject(), event)
        person.parents.add(parent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(-2))
    def test_privatize_person_with_grandparent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person('P0')
        person.privacy = privacy
        parent = Person('P1')
        person.parents.add(parent)
        grandparent = Person('P2')
        if event is not None:
            Presence(None, grandparent, Subject(), event)
        parent.parents.add(grandparent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    @pytest.mark.parametrize('expected, privacy, event', _expand_person(-3))
    def test_privatize_person_with_great_grandparent(
        self,
        expected: bool,
        privacy: Privacy,
        event: Event | None,
    ) -> None:
        person = Person('P0')
        person.privacy = privacy
        parent = Person('P1')
        person.parents.add(parent)
        grandparent = Person('P2')
        parent.parents.add(grandparent)
        great_grandparent = Person('P2')
        if event is not None:
            Presence(None, great_grandparent, Subject(), event)
        grandparent.parents.add(great_grandparent)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(person)
        assert expected == person.private

    def test_privatize_event_should_not_privatize_if_public(self) -> None:
        source_file = File('F0', Path(__file__))
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File('F1', Path(__file__))
        citation = Citation('C0', source)
        citation.files.add(citation_file)
        event_file = File('F1', Path(__file__))
        event = Event('E1', Birth)
        event.public = True
        event.citations.add(citation)
        event.files.add(event_file)
        person = Person('P0')
        Presence(None, person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(event)
        assert not event.private
        assert event_file.privacy is Privacy.UNDETERMINED
        assert citation.privacy is Privacy.UNDETERMINED
        assert source.privacy is Privacy.UNDETERMINED
        assert citation_file.privacy is Privacy.UNDETERMINED
        assert source_file.privacy is Privacy.UNDETERMINED
        assert person.privacy is Privacy.UNDETERMINED

    def test_privatize_event_should_privatize_if_private(self) -> None:
        source_file = File('F0', Path(__file__))
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File('F1', Path(__file__))
        citation = Citation('C0', source)
        citation.files.add(citation_file)
        event_file = File('F1', Path(__file__))
        event = Event('E1', Birth)
        event.private = True
        event.citations.add(citation)
        event.files.add(event_file)
        person = Person('P0')
        Presence(None, person, Subject(), event)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(event)
        assert event.private
        assert event_file.private
        assert citation.private
        assert source.private
        assert citation_file.private
        assert source_file.private
        assert person.privacy is Privacy.UNDETERMINED

    def test_privatize_source_should_not_privatize_if_public(self) -> None:
        file = File('F0', Path(__file__))
        source = Source('S0', 'The Source')
        source.public = True
        source.files.add(file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(source)
        assert not source.private
        assert file.privacy is Privacy.UNDETERMINED

    def test_privatize_source_should_privatize_if_private(self) -> None:
        file = File('F0', Path(__file__))
        source = Source('S0', 'The Source')
        source.private = True
        source.files.add(file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(source)
        assert source.private
        assert file.private

    def test_privatize_citation_should_not_privatize_if_public(self) -> None:
        source_file = File('F0', Path(__file__))
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File('F1', Path(__file__))
        citation = Citation('C0', source)
        citation.public = True
        citation.files.add(citation_file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(citation)
        assert not citation.private
        assert source.privacy is Privacy.UNDETERMINED
        assert citation_file.privacy is Privacy.UNDETERMINED
        assert source_file.privacy is Privacy.UNDETERMINED

    def test_privatize_citation_should_privatize_if_private(self) -> None:
        source_file = File('F0', Path(__file__))
        source = Source('The Source')
        source.files.add(source_file)
        citation_file = File('F1', Path(__file__))
        citation = Citation('C0', source)
        citation.private = True
        citation.files.add(citation_file)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(citation)
        assert citation.private
        assert source.private
        assert citation_file.private
        assert source_file.private

    def test_privatize_file_should_not_privatize_if_public(self) -> None:
        source = Source(None, 'The Source')
        citation = Citation(None, source)
        file = File('F0', Path(__file__))
        file.public = True
        file.citations.add(citation)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(file)
        assert not file.private
        assert citation.privacy is Privacy.UNDETERMINED

    def test_privatize_file_should_privatize_if_private(self) -> None:
        source = Source(None, 'The Source')
        citation = Citation(None, source)
        file = File('F0', Path(__file__))
        file.private = True
        file.citations.add(citation)
        Privatizer(DEFAULT_LIFETIME_THRESHOLD).privatize(file)
        assert file.private
        assert citation.private
