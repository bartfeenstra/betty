from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Optional
from unittest import TestCase

from parameterized import parameterized

from betty.ancestry import Ancestry, Person, Event, Presence
from betty.config import Configuration
from betty.locale import Date
from betty.parse import parse
from betty.plugins.privatizer import Privatizer
from betty.site import Site


def _expand(generation: int):
    multiplier = abs(generation) + 1 if generation < 0 else 1
    threshold_year = datetime.now().year - 100 * multiplier
    date_under_threshold = Date(threshold_year + 1, 1, 1)
    date_over_threshold = Date(threshold_year - 1, 1, 1)
    return parameterized.expand([
        # If there are no events for a person, their privacy does not change.
        (True, None, None),
        (True, True, None),
        (False, False, None),
        # Deaths are special, and their existence prevents generation 0 from being private even without a date.
        (generation != 0, None, Event('E0', Event.Type.DEATH)),
        (True, True, Event('E0', Event.Type.DEATH)),
        (False, False, Event('E0', Event.Type.DEATH)),
        # Regular events without dates do not affect privacy.
        (True, None, Event('E0', Event.Type.BIRTH)),
        (True, True, Event('E0', Event.Type.BIRTH)),
        (False, False, Event('E0', Event.Type.BIRTH)),
        # Regular events with incomplete dates do not affect privacy.
        (True, None, Event('E0', Event.Type.BIRTH, date=Date())),
        (True, True, Event('E0', Event.Type.BIRTH, date=Date())),
        (False, False, Event('E0', Event.Type.BIRTH, date=Date())),
        # Regular events under the lifetime threshold do not affect privacy.
        (True, None, Event('E0', Event.Type.BIRTH, date=date_under_threshold)),
        (True, True, Event('E0', Event.Type.BIRTH, date=date_under_threshold)),
        (False, False, Event('E0', Event.Type.BIRTH, date=date_under_threshold)),
        # Regular events over the lifetime threshold affect privacy.
        (False, None, Event('E0', Event.Type.BIRTH, date=date_over_threshold)),
        (True, True, Event('E0', Event.Type.BIRTH, date=date_over_threshold)),
        (False, False, Event('E0', Event.Type.BIRTH, date=date_over_threshold)),
    ])


class PrivatizerTest(TestCase):
    def test_post_parse(self):
        with TemporaryDirectory() as output_directory_path:
            configuration = Configuration(
                output_directory_path, 'https://example.com')
            configuration.plugins[Privatizer] = {}
            site = Site(configuration)
            person = Person('P0')
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = Event('E0', Event.Type.BIRTH)
            person.presences.append(presence)
            site.ancestry.people[person.id] = person
            parse(site)
            self.assertTrue(person.private)

    @_expand(0)
    def test_privatize_without_relatives(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        if event is not None:
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = event
            person.presences.append(presence)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand(1)
    def test_privatize_with_child(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        if event is not None:
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = event
            child.presences.append(presence)
        person.children.append(child)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        ancestry.people[child.id] = child
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand(2)
    def test_privatize_with_grandchild(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        person.children.append(child)
        grandchild = Person('P2')
        if event is not None:
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = event
            grandchild.presences.append(presence)
        child.children.append(grandchild)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        ancestry.people[child.id] = child
        ancestry.people[grandchild.id] = grandchild
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand(3)
    def test_privatize_with_great_grandchild(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        child = Person('P1')
        person.children.append(child)
        grandchild = Person('P2')
        child.children.append(grandchild)
        great_grandchild = Person('P2')
        if event is not None:
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = event
            great_grandchild.presences.append(presence)
        grandchild.children.append(great_grandchild)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand(-1)
    def test_privatize_with_parent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        if event is not None:
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = event
            parent.presences.append(presence)
        person.parents.append(parent)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        ancestry.people[parent.id] = parent
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand(-2)
    def test_privatize_with_grandparent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        person.parents.append(parent)
        grandparent = Person('P2')
        if event is not None:
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = event
            grandparent.presences.append(presence)
        parent.parents.append(grandparent)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        ancestry.people[parent.id] = parent
        ancestry.people[grandparent.id] = grandparent
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)

    @_expand(-3)
    def test_privatize_with_great_grandparent(self, expected, private, event: Optional[Event]):
        person = Person('P0')
        person.private = private
        parent = Person('P1')
        person.parents.append(parent)
        grandparent = Person('P2')
        parent.parents.append(grandparent)
        great_grandparent = Person('P2')
        if event is not None:
            presence = Presence(Presence.Role.SUBJECT)
            presence.event = event
            great_grandparent.presences.append(presence)
        grandparent.parents.append(great_grandparent)
        ancestry = Ancestry()
        ancestry.people[person.id] = person
        sut = Privatizer()
        sut.privatize(ancestry)
        self.assertEquals(expected, person.private)
