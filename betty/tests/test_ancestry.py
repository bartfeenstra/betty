from tempfile import TemporaryFile, NamedTemporaryFile
from unittest import TestCase
from unittest.mock import Mock

from parameterized import parameterized

from betty.ancestry import EventHandlingSetList, Person, Event, Place, File, Note, Presence, LocalizedName, PersonName, \
    IdentifiableEvent
from betty.locale import Date


class EventHandlingSetTest(TestCase):
    def test_list(self):
        sut = EventHandlingSetList(lambda _: None, lambda _: None)
        value = 'Some value'
        sut.append(value)
        self.assertEquals([value], sut.list)

    def test_with_handler(self):
        reference = []

        def addition_handler(added_value):
            reference.append(added_value)

        def removal_handler(removed_value):
            reference.remove(removed_value)

        sut = EventHandlingSetList(addition_handler, removal_handler)

        value = 'A valuable value'

        sut.append(value)
        self.assertCountEqual([value], sut)
        self.assertEquals([value], reference)

        newvalue = 'A even more valuable value'

        sut.replace([newvalue])
        self.assertCountEqual([newvalue], sut)
        self.assertEquals([newvalue], reference)

        sut.remove(newvalue)
        self.assertCountEqual([], sut)
        self.assertEquals([], reference)


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
        event = Event(Event.Type.BIRTH)
        sut = Person('1')
        presence = Presence(sut, Presence.Role.SUBJECT, event)
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
        sut = Place('1', [LocalizedName('one')])
        event = IdentifiableEvent('1', Event.Type.BIRTH)
        sut.events.append(event)
        self.assertIn(event, sut.events)
        self.assertEquals(sut, event.place)
        sut.events.remove(event)
        self.assertCountEqual([], sut.events)
        self.assertEquals(None, event.place)

    def test_encloses_should_sync_references(self):
        sut = Place('1', [LocalizedName('one')])
        enclosed_place = Place('2', [LocalizedName('two')])
        sut.encloses.append(enclosed_place)
        self.assertIn(enclosed_place, sut.encloses)
        self.assertEquals(sut, enclosed_place.enclosed_by)
        sut.encloses.remove(enclosed_place)
        self.assertCountEqual([], sut.encloses)
        self.assertEquals(None, enclosed_place.enclosed_by)

    def test_enclosed_by_should_sync_references(self):
        sut = Place('1', [LocalizedName('one')])
        enclosing_place = Place('2', [LocalizedName('two')])
        sut.enclosed_by = enclosing_place
        self.assertEquals(enclosing_place, sut.enclosed_by)
        self.assertIn(sut, enclosing_place.encloses)
        sut.enclosed_by = None
        self.assertIsNone(sut.enclosed_by)
        self.assertCountEqual([], enclosing_place.encloses)


class EventTest(TestCase):
    def test_date(self):
        sut = IdentifiableEvent('1', Event.Type.BIRTH)
        self.assertIsNone(sut.date)
        date = Mock(Date)
        sut.date = date
        self.assertEquals(date, sut.date)

    def test_type(self):
        event_type = Event.Type.BIRTH
        sut = IdentifiableEvent('1', event_type)
        self.assertEquals(event_type, sut.type)

    def test_place_should_sync_references(self):
        place = Place('1', [LocalizedName('one')])
        sut = IdentifiableEvent('1', Event.Type.BIRTH)
        sut.place = place
        self.assertEquals(place, sut.place)
        self.assertIn(sut, place.events)
        sut.place = None
        self.assertEquals(None, sut.place)
        self.assertNotIn(sut, place.events)

    def test_presence_should_sync_references(self):
        person = Person('P1')
        sut = IdentifiableEvent('1', Event.Type.BIRTH)
        presence = Presence(person, Presence.Role.SUBJECT, sut)
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
        (True, LocalizedName('Ikke'), LocalizedName('Ikke')),
        (True, LocalizedName('Ikke', 'nl-NL'), LocalizedName('Ikke', 'nl-NL')),
        (False, LocalizedName('Ikke', 'nl-NL'), LocalizedName('Ikke', 'nl-BE')),
        (False, LocalizedName('Ikke', 'nl-NL'), LocalizedName('Ik', 'nl-NL')),
        (False, LocalizedName('Ikke'), LocalizedName('Ik')),
    ])
    def test_eq(self, expected, a, b):
        self.assertEquals(expected, a == b)

    def test_str(self):
        name = 'Ikke'
        sut = LocalizedName(name)
        self.assertEquals(name, str(sut))

    def test_name(self):
        name = 'Ikke'
        sut = LocalizedName(name)
        self.assertEquals(name, sut.name)
