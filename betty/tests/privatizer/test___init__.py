from datetime import datetime
from typing import Optional

import pytest

from betty.app import App
from betty.load import load
from betty.locale import Date, DateRange
from betty.model.ancestry import Person, Presence, Event, Source, File, Subject, Attendee, Citation, Ancestry
from betty.model.event_type import Death, Birth, Marriage
from betty.privatizer import Privatizer, privatize
from betty.project import ProjectExtensionConfiguration


def _expand_person(generation: int):
    lifetime_threshold = 125
    multiplier = abs(generation) + 1 if generation < 0 else 1
    lifetime_threshold_year = datetime.now().year - lifetime_threshold * multiplier
    date_under_lifetime_threshold = Date(lifetime_threshold_year + 1, 1, 1)
    date_range_start_under_lifetime_threshold = DateRange(date_under_lifetime_threshold)
    date_range_end_under_lifetime_threshold = DateRange(None, date_under_lifetime_threshold)
    date_over_lifetime_threshold = Date(lifetime_threshold_year - 1, 1, 1)
    date_range_start_over_lifetime_threshold = DateRange(date_over_lifetime_threshold)
    date_range_end_over_lifetime_threshold = DateRange(None, date_over_lifetime_threshold)
    return [
        # If there are no events for a person, they are private.
        (True, None, None),
        (True, True, None),
        (False, False, None),

        # Deaths and other end-of-life events are special, but only for the person whose privacy is being checked:
        # - If they're present without dates, the person isn't private.
        # - If they're present and their dates or date ranges' end dates are in the past, the person isn't private.
        (generation != 0, None, Event(None, Death(), date=Date(datetime.now().year, datetime.now().month, datetime.now().day))),
        (generation != 0, None, Event(None, Death(), date=date_under_lifetime_threshold)),
        (True, None, Event(None, Death(), date=date_range_start_under_lifetime_threshold)),
        (generation != 0, None, Event(None, Death(), date=date_range_end_under_lifetime_threshold)),
        (False, None, Event(None, Death(), date=date_over_lifetime_threshold)),
        (True, None, Event(None, Death(), date=date_range_start_over_lifetime_threshold)),
        (False, None, Event(None, Death(), date=date_range_end_over_lifetime_threshold)),
        (True, True, Event(None, Death())),
        (False, False, Event(None, Death())),
        (generation != 0, None, Event(None, Death())),

        # Regular events without dates do not affect privacy.
        (True, None, Event(None, Birth())),
        (True, True, Event(None, Birth())),
        (False, False, Event(None, Birth())),

        # Regular events with incomplete dates do not affect privacy.
        (True, None, Event(None, Birth(), date=Date())),
        (True, True, Event(None, Birth(), date=Date())),
        (False, False, Event(None, Birth(), date=Date())),

        # Regular events under the lifetime threshold do not affect privacy.
        (True, None, Event(None, Birth(), date=date_under_lifetime_threshold)),
        (True, True, Event(None, Birth(), date=date_under_lifetime_threshold)),
        (False, False, Event(None, Birth(), date=date_under_lifetime_threshold)),
        (True, None, Event(None, Birth(), date=date_range_start_under_lifetime_threshold)),
        (True, True, Event(None, Birth(), date=date_range_start_under_lifetime_threshold)),
        (False, False, Event(None, Birth(), date=date_range_start_under_lifetime_threshold)),
        (True, None, Event(None, Birth(), date=date_range_end_under_lifetime_threshold)),
        (True, True, Event(None, Birth(), date=date_range_end_under_lifetime_threshold)),
        (False, False, Event(None, Birth(), date=date_range_end_under_lifetime_threshold)),

        # Regular events over the lifetime threshold affect privacy.
        (False, None, Event(None, Birth(), date=date_over_lifetime_threshold)),
        (True, True, Event(None, Birth(), date=date_over_lifetime_threshold)),
        (False, False, Event(None, Birth(), date=date_over_lifetime_threshold)),
        (True, None, Event(None, Birth(), date=date_range_start_over_lifetime_threshold)),
        (True, True, Event(None, Birth(), date=date_range_start_over_lifetime_threshold)),
        (False, False, Event(None, Birth(), date=date_range_start_over_lifetime_threshold)),
        (False, None, Event(None, Birth(), date=date_range_end_over_lifetime_threshold)),
        (True, True, Event(None, Birth(), date=date_range_end_over_lifetime_threshold)),
        (False, False, Event(None, Birth(), date=date_range_end_over_lifetime_threshold)),
    ]


class TestPrivatizer:
    async def test_post_load(self):
        person = Person('P0')
        Presence(person, Subject(), Event(None, Birth()))

        source_file = File('F0', __file__)
        source = Source('S0', 'The Source')
        source.private = True
        source.files.append(source_file)

        citation_file = File('F0', __file__)
        citation_source = Source('The Source')
        citation = Citation('C0', citation_source)
        citation.private = True
        citation.files.append(citation_file)

        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Privatizer))
            app.project.ancestry.entities.append(person)
            app.project.ancestry.entities.append(source)
            app.project.ancestry.entities.append(citation)
            await load(app)

            assert person.private
            assert source_file.private
            assert citation_file.private

    def test_privatize_person_should_not_privatize_if_public(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = Citation('C0', source)
        citation.files.append(citation_file)
        event_as_subject = Event(None, Birth())
        event_as_attendee = Event(None, Marriage())
        person_file = File('F2', __file__)
        person = Person('P0')
        person.private = False
        person.citations.append(citation)
        person.files.append(person_file)
        Presence(person, Subject(), event_as_subject)
        Presence(person, Attendee(), event_as_attendee)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert not person.private
        assert citation.private is None
        assert source.private is None
        assert person_file.private is None
        assert citation_file.private is None
        assert source_file.private is None
        assert event_as_subject.private is None
        assert event_as_attendee.private is None

    def test_privatize_person_should_privatize_if_private(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = Citation('C0', source)
        citation.files.append(citation_file)
        event_as_subject = Event(None, Birth())
        event_as_attendee = Event(None, Marriage())
        person_file = File('F2', __file__)
        person = Person('P0')
        person.private = True
        person.citations.append(citation)
        person.files.append(person_file)
        Presence(person, Subject(), event_as_subject)
        Presence(person, Attendee(), event_as_attendee)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert person.private
        assert citation.private
        assert source.private
        assert person_file.private
        assert citation_file.private
        assert source_file.private
        assert event_as_subject.private
        assert event_as_attendee.private is None

    @pytest.mark.parametrize('expected, private, event', _expand_person(0))
    def test_privatize_person_without_relatives(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        if event is not None:
            Presence(person, Subject(), event)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert expected == person.private

    @pytest.mark.parametrize('expected, private, event', _expand_person(1))
    def test_privatize_person_with_child(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        if event is not None:
            Presence(child, Subject(), event)
        person.children.append(child)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert expected == person.private

    @pytest.mark.parametrize('expected, private, event', _expand_person(2))
    def test_privatize_person_with_grandchild(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        person.children.append(child)
        grandchild = Person('P2')
        if event is not None:
            Presence(grandchild, Subject(), event)
        child.children.append(grandchild)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert expected == person.private

    @pytest.mark.parametrize('expected, private, event', _expand_person(3))
    def test_privatize_person_with_great_grandchild(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        person.children.append(child)
        grandchild = Person('P2')
        child.children.append(grandchild)
        great_grandchild = Person('P2')
        if event is not None:
            Presence(great_grandchild, Subject(), event)
        grandchild.children.append(great_grandchild)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert expected == person.private

    @pytest.mark.parametrize('expected, private, event', _expand_person(-1))
    def test_privatize_person_with_parent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        if event is not None:
            Presence(parent, Subject(), event)
        person.parents.append(parent)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert expected == person.private

    @pytest.mark.parametrize('expected, private, event', _expand_person(-2))
    def test_privatize_person_with_grandparent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        person.parents.append(parent)
        grandparent = Person('P2')
        if event is not None:
            Presence(grandparent, Subject(), event)
        parent.parents.append(grandparent)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert expected == person.private

    @pytest.mark.parametrize('expected, private, event', _expand_person(-3))
    def test_privatize_person_with_great_grandparent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        person.parents.append(parent)
        grandparent = Person('P2')
        parent.parents.append(grandparent)
        great_grandparent = Person('P2')
        if event is not None:
            Presence(great_grandparent, Subject(), event)
        grandparent.parents.append(great_grandparent)
        ancestry = Ancestry()
        ancestry.entities.append(person)
        privatize(ancestry)
        assert expected == person.private

    def test_privatize_event_should_not_privatize_if_public(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = Citation('C0', source)
        citation.files.append(citation_file)
        event_file = File('F1', __file__)
        event = Event('E1', Birth())
        event.private = False
        event.citations.append(citation)
        event.files.append(event_file)
        person = Person('P0')
        Presence(person, Subject(), event)
        ancestry = Ancestry()
        ancestry.entities.append(event)
        privatize(ancestry)
        assert not event.private
        assert event_file.private is None
        assert citation.private is None
        assert source.private is None
        assert citation_file.private is None
        assert source_file.private is None
        assert person.private is None

    def test_privatize_event_should_privatize_if_private(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = Citation('C0', source)
        citation.files.append(citation_file)
        event_file = File('F1', __file__)
        event = Event('E1', Birth())
        event.private = True
        event.citations.append(citation)
        event.files.append(event_file)
        person = Person('P0')
        Presence(person, Subject(), event)
        ancestry = Ancestry()
        ancestry.entities.append(event)
        privatize(ancestry)
        assert event.private
        assert event_file.private
        assert citation.private
        assert source.private
        assert citation_file.private
        assert source_file.private
        assert person.private is None

    def test_privatize_source_should_not_privatize_if_public(self):
        file = File('F0', __file__)
        source = Source('S0', 'The Source')
        source.private = False
        source.files.append(file)
        ancestry = Ancestry()
        ancestry.entities.append(source)
        privatize(ancestry)
        assert not source.private
        assert file.private is None

    def test_privatize_source_should_privatize_if_private(self):
        file = File('F0', __file__)
        source = Source('S0', 'The Source')
        source.private = True
        source.files.append(file)
        ancestry = Ancestry()
        ancestry.entities.append(source)
        privatize(ancestry)
        assert source.private
        assert file.private

    def test_privatize_citation_should_not_privatize_if_public(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = Citation('C0', source)
        citation.private = False
        citation.files.append(citation_file)
        ancestry = Ancestry()
        ancestry.entities.append(citation)
        privatize(ancestry)
        assert not citation.private
        assert source.private is None
        assert citation_file.private is None
        assert source_file.private is None

    def test_privatize_citation_should_privatize_if_private(self):
        source_file = File('F0', __file__)
        source = Source('The Source')
        source.files.append(source_file)
        citation_file = File('F1', __file__)
        citation = Citation('C0', source)
        citation.private = True
        citation.files.append(citation_file)
        ancestry = Ancestry()
        ancestry.entities.append(citation)
        privatize(ancestry)
        assert citation.private
        assert source.private
        assert citation_file.private
        assert source_file.private

    def test_privatize_file_should_not_privatize_if_public(self):
        source = Source(None, 'The Source')
        citation = Citation(None, source)
        file = File('F0', __file__)
        file.private = False
        file.citations.append(citation)
        ancestry = Ancestry()
        ancestry.entities.append(file)
        privatize(ancestry)
        assert not file.private
        assert citation.private is None

    def test_privatize_file_should_privatize_if_private(self):
        source = Source(None, 'The Source')
        citation = Citation(None, source)
        file = File('F0', __file__)
        file.private = True
        file.citations.append(citation)
        ancestry = Ancestry()
        ancestry.entities.append(file)
        privatize(ancestry)
        assert True, file.private
        assert citation.private
