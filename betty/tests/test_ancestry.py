from tempfile import TemporaryFile, NamedTemporaryFile
from unittest import TestCase
from unittest.mock import Mock

from parameterized import parameterized

from betty.ancestry import EventHandlingSetList, Person, Event, Place, File, Note, Presence, PlaceName, PersonName, \
    IdentifiableEvent, Subject, Birth, Enclosure
from betty.locale import Date


class EventHandlingSetListTest(TestCase):
    def test_prepend(self):
        added = []
        removal_handler = Mock()
        sut = EventHandlingSetList(lambda value: added.append(value), removal_handler)
        sut.prepend(3)
        sut.prepend(2)
        sut.prepend(1)
        # Prepend an already prepended value again, and assert that it was ignored.
        sut.prepend(1)
        self.assertSequenceEqual([1, 2, 3], sut)
        self.assertSequenceEqual([3, 2, 1], added)
        removal_handler.assert_not_called()

    def test_append(self):
        added = []
        removal_handler = Mock()
        sut = EventHandlingSetList(lambda value: added.append(value), removal_handler)
        sut.append(3)
        sut.append(2)
        sut.append(1)
        # Append an already appended value again, and assert that it was ignored.
        sut.append(1)
        self.assertSequenceEqual([3, 2, 1], sut)
        self.assertSequenceEqual([3, 2, 1], added)
        removal_handler.assert_not_called()

    def test_remove(self):
        added = []
        removed = []
        sut = EventHandlingSetList(lambda value: added.append(value), lambda value: removed.append(value))
        sut.append(1, 2, 3, 4)
        sut.remove(4, 2)
        self.assertSequenceEqual([1, 3], sut)
        self.assertSequenceEqual([1, 2, 3, 4], added)
        self.assertSequenceEqual([4, 2], removed)

    def test_replace(self):
        added = []
        removed = []
        sut = EventHandlingSetList(lambda value: added.append(value), lambda value: removed.append(value))
        sut.append(1, 2, 3)
        sut.replace(4, 5, 6)
        self.assertSequenceEqual([4, 5, 6], sut)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6], added)
        self.assertSequenceEqual([1, 2, 3], removed)

    def test_clear(self):
        added = []
        removed = []
        sut = EventHandlingSetList(lambda value: added.append(value), lambda value: removed.append(value))
        sut.append(1, 2, 3)
        sut.clear()
        self.assertSequenceEqual([], sut)
        self.assertSequenceEqual([1, 2, 3], added)
        self.assertSequenceEqual([1, 2, 3], removed)

    def test_list(self):
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        sut.append(1, 2, 3)
        self.assertEqual([1, 2, 3], sut.list)

    def test_len(self):
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        sut.append(1, 2, 3)
        self.assertEqual(3, len(sut))

    def test_iter(self):
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        sut.append(1, 2, 3)
        # list() gets all items through __iter__ and stores them in the same order.
        self.assertSequenceEqual([1, 2, 3], list(sut))

    def test_getitem(self):
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        sut.append(1, 2, 3)
        self.assertEqual(1, sut[0])
        self.assertEqual(2, sut[1])
        self.assertEqual(3, sut[2])
        with self.assertRaises(IndexError):
            sut[3]

    def test_set_like_functionality(self):
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        # Ensure duplicates are skipped.
        sut.append(1, 2, 3, 1, 2, 3, 1, 2, 3)
        # Ensure skipped duplicates do not affect further new values.
        sut.append(1, 2, 3, 4, 5, 6, 7, 8, 9)
        self.assertSequenceEqual([1, 2, 3, 4, 5, 6, 7, 8, 9], sut)


class PersonTest(TestCase):
    def test_names_should_sync_references(self):
        sut = Person('1')
        name = PersonName('Janet', 'Not a Girl')
        sut.names.append(name)
        self.assertCountEqual([name], sut.names)
        self.assertEquals(sut, name.person)
        sut.names.remove(name)
        self.assertCountEqual([], sut.names)
        self.assertIsNone(name.person)

    def test_parents_should_sync_references(self):
        sut = Person('1')
        parent = Person('2')
        sut.parents.append(parent)
        self.assertCountEqual([parent], sut.parents)
        self.assertCountEqual([sut], parent.children)
        sut.parents.remove(parent)
        self.assertCountEqual([], sut.parents)
        self.assertCountEqual([], parent.children)

    def test_children_should_sync_references(self):
        sut = Person('1')
        child = Person('2')
        sut.children.append(child)
        self.assertCountEqual([child], sut.children)
        self.assertCountEqual([sut], child.parents)
        sut.children.remove(child)
        self.assertCountEqual([], sut.children)
        self.assertCountEqual([], child.parents)

    def test_siblings_without_parents(self):
        sut = Person('person')
        self.assertCountEqual([], sut.siblings)

    def test_siblings_with_one_common_parent(self):
        sut = Person('1')
        sibling = Person('2')
        parent = Person('3')
        parent.children = [sut, sibling]

        self.assertCountEqual([sibling], sut.siblings)

    def test_siblings_with_multiple_common_parents(self):
        sut = Person('1')
        sibling = Person('2')
        parent = Person('3')
        parent.children = [sut, sibling]

        self.assertCountEqual([sibling], sut.siblings)

    def test_presence_should_sync_references(self):
        event = Event(Birth())
        sut = Person('1')
        presence = Presence(sut, Subject(), event)
        sut.presences.append(presence)
        self.assertCountEqual([presence], sut.presences)
        self.assertEquals(sut, presence.person)
        sut.presences.remove(presence)
        self.assertCountEqual([], sut.presences)
        self.assertIsNone(presence.person)


class PersonNameTest(TestCase):
    def test_person_should_sync_references(self):
        sut = PersonName('Janet', 'Not a Girl')
        person = Person('1')
        sut.person = person
        self.assertEquals(person, sut.person)
        self.assertCountEqual([sut], person.names)
        sut.person = None
        self.assertIsNone(sut.person)
        self.assertCountEqual([], person.names)


class PlaceTest(TestCase):
    def test_events_should_sync_references(self):
        sut = Place('1', [PlaceName('one')])
        event = IdentifiableEvent('1', Birth())
        sut.events.append(event)
        self.assertIn(event, sut.events)
        self.assertEquals(sut, event.place)
        sut.events.remove(event)
        self.assertCountEqual([], sut.events)
        self.assertEquals(None, event.place)

    def test_encloses_should_sync_references(self):
        sut = Place('1', [PlaceName('one')])
        enclosed_place = Place('2', [PlaceName('two')])
        enclosure = Enclosure(enclosed_place, sut)
        self.assertIn(enclosure, sut.encloses)
        self.assertEquals(sut, enclosure.enclosed_by)
        sut.encloses.remove(enclosure)
        self.assertCountEqual([], sut.encloses)
        self.assertIsNone(enclosure.enclosed_by)

    def test_enclosed_by_should_sync_references(self):
        sut = Place('1', [PlaceName('one')])
        enclosing_place = Place('2', [PlaceName('two')])
        enclosure = Enclosure(sut, enclosing_place)
        self.assertIn(enclosure, sut.enclosed_by)
        self.assertEquals(sut, enclosure.encloses)
        sut.enclosed_by.remove(enclosure)
        self.assertCountEqual([], sut.enclosed_by)
        self.assertIsNone(enclosure.encloses)


class EventTest(TestCase):
    def test_date(self):
        sut = IdentifiableEvent('1', Birth())
        self.assertIsNone(sut.date)
        date = Mock(Date)
        sut.date = date
        self.assertEquals(date, sut.date)

    def test_type(self):
        event_type = Birth()
        sut = IdentifiableEvent('1', event_type)
        self.assertEquals(event_type, sut.type)

    def test_place_should_sync_references(self):
        place = Place('1', [PlaceName('one')])
        sut = IdentifiableEvent('1', Birth())
        sut.place = place
        self.assertEquals(place, sut.place)
        self.assertIn(sut, place.events)
        sut.place = None
        self.assertEquals(None, sut.place)
        self.assertNotIn(sut, place.events)

    def test_presence_should_sync_references(self):
        person = Person('P1')
        sut = IdentifiableEvent('1', Birth())
        presence = Presence(person, Subject(), sut)
        sut.presences.append(presence)
        self.assertCountEqual([presence], sut.presences)
        self.assertEquals(sut, presence.event)
        sut.presences.remove(presence)
        self.assertCountEqual([], sut.presences)
        self.assertIsNone(presence.event)


class NoteTest(TestCase):
    def test_text(self):
        text = 'Betty wrote this.'
        sut = Note(text)
        self.assertEquals(text, sut.text)


class FileTest(TestCase):
    def test_id(self):
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertEquals(file_id, sut.id)

    def test_path(self):
        with TemporaryFile() as f:
            file_id = 'BETTY01'
            sut = File(file_id, f.name)
            self.assertEquals(f.name, sut.path)

    def test_extension_with_extension(self):
        extension = 'betty'
        with NamedTemporaryFile(suffix='.%s' % extension) as f:
            file_id = 'BETTY01'
            sut = File(file_id, f.name)
            self.assertEquals(extension, sut.extension)

    def test_extension_without_extension(self):
        with NamedTemporaryFile() as f:
            file_id = 'BETTY01'
            sut = File(file_id, f.name)
            self.assertIsNone(sut.extension)

    def test_description(self):
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        description = 'Hi, my name is Betty!'
        sut.description = description
        self.assertEquals(description, sut.description)

    def test_notes(self):
        file_id = 'BETTY01'
        file_path = '/tmp/betty'
        sut = File(file_id, file_path)
        self.assertCountEqual([], sut.notes)
        notes = (Mock(Note), Mock(Note))
        sut.notes = notes
        self.assertCountEqual(notes, sut.notes)


class LocalizedNameTest(TestCase):
    @parameterized.expand([
        (True, PlaceName('Ikke'), PlaceName('Ikke')),
        (True, PlaceName('Ikke', 'nl-NL'), PlaceName('Ikke', 'nl-NL')),
        (False, PlaceName('Ikke', 'nl-NL'), PlaceName('Ikke', 'nl-BE')),
        (False, PlaceName('Ikke', 'nl-NL'), PlaceName('Ik', 'nl-NL')),
        (False, PlaceName('Ikke'), PlaceName('Ik')),
    ])
    def test_eq(self, expected, a, b):
        self.assertEquals(expected, a == b)

    def test_str(self):
        name = 'Ikke'
        sut = PlaceName(name)
        self.assertEquals(name, str(sut))

    def test_name(self):
        name = 'Ikke'
        sut = PlaceName(name)
        self.assertEquals(name, sut.name)


class PresenceTest(TestCase):
    def test_event_deletion_upon_person_deletion(self) -> None:
        person = Person('P1')
        event = Event(Birth())
        sut = Presence(person, Subject(), event)
        del sut.person
        self.assertIsNone(sut.event)
        self.assertNotIn(sut, event.presences)

    def test_event_deletion_upon_person_set_to_none(self) -> None:
        person = Person('P1')
        event = Event(Birth())
        sut = Presence(person, Subject(), event)
        sut.person = None
        self.assertIsNone(sut.event)
        self.assertNotIn(sut, event.presences)

    def test_person_deletion_upon_event_deletion(self) -> None:
        person = Person('P1')
        event = Event(Birth())
        sut = Presence(person, Subject(), event)
        del sut.event
        self.assertIsNone(sut.person)
        self.assertNotIn(sut, person.presences)

    def test_person_deletion_upon_event_set_to_none(self) -> None:
        person = Person('P1')
        event = Event(Birth())
        sut = Presence(person, Subject(), event)
        sut.event = None
        self.assertIsNone(sut.person)
        self.assertNotIn(sut, person.presences)
