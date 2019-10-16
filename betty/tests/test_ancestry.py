from tempfile import TemporaryFile, NamedTemporaryFile
from unittest import TestCase
from unittest.mock import Mock

from parameterized import parameterized

from betty.ancestry import EventHandlingSet, Person, Event, Place, Date, File, Note, Presence, LocalizedName


class EventHandlingSetTest(TestCase):
    def test_list(self):
        sut = EventHandlingSet()
        value = 'Some value'
        sut.add(value)
        self.assertEquals([value], sut.list)

    def test_with_handler(self):
        reference = []

        def addition_handler(added_value):
            reference.append(added_value)

        def removal_handler(removed_value):
            reference.remove(removed_value)

        sut = EventHandlingSet(addition_handler, removal_handler)

        value = 'A valuable value'

        sut.add(value)
        self.assertCountEqual([value], sut)
        self.assertEquals([value], reference)

        newvalue = 'A even more valuable value'

        sut.replace([newvalue])
        self.assertCountEqual([newvalue], sut)
        self.assertEquals([newvalue], reference)

        sut.remove(newvalue)
        self.assertCountEqual([], sut)
        self.assertEquals([], reference)

    def test_without_handler(self):
        sut = EventHandlingSet()
        value = 'A valuable value'
        sut.add(value)
        self.assertCountEqual([value], sut)
        sut.remove(value)
        self.assertCountEqual([], sut)


class PersonTest(TestCase):
    def test_parents_should_sync_references(self):
        sut = Person('1', 'one')
        parent = Person('2', 'two')
        sut.parents.add(parent)
        self.assertCountEqual([parent], sut.parents)
        self.assertCountEqual([sut], parent.children)
        sut.parents.remove(parent)
        self.assertCountEqual([], sut.parents)
        self.assertCountEqual([], parent.children)

    def test_children_should_sync_references(self):
        sut = Person('1')
        child = Person('2')
        sut.children.add(child)
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
        presence = Presence(Presence.Role.SUBJECT)
        sut = Person('1')
        sut.presences.add(presence)
        self.assertCountEqual([presence], sut.presences)
        self.assertEquals(sut, presence.person)
        sut.presences.remove(presence)
        self.assertCountEqual([], sut.presences)
        self.assertIsNone(presence.person)


class PlaceTest(TestCase):
    def test_events_should_sync_references(self):
        sut = Place('1', [LocalizedName('one')])
        event = Event('1', Event.Type.BIRTH)
        sut.events.add(event)
        self.assertIn(event, sut.events)
        self.assertEquals(sut, event.place)
        sut.events.remove(event)
        self.assertCountEqual([], sut.events)
        self.assertEquals(None, event.place)

    def test_encloses_should_sync_references(self):
        sut = Place('1', [LocalizedName('one')])
        enclosed_place = Place('2', [LocalizedName('two')])
        sut.encloses.add(enclosed_place)
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
        sut = Event('1', Event.Type.BIRTH)
        self.assertIsNone(sut.date)
        date = Mock(Date)
        sut.date = date
        self.assertEquals(date, sut.date)

    def test_type(self):
        event_type = Event.Type.BIRTH
        sut = Event('1', event_type)
        self.assertEquals(event_type, sut.type)

    def test_place_should_sync_references(self):
        place = Place('1', [LocalizedName('one')])
        sut = Event('1', Event.Type.BIRTH)
        sut.place = place
        self.assertEquals(place, sut.place)
        self.assertIn(sut, place.events)
        sut.place = None
        self.assertEquals(None, sut.place)
        self.assertNotIn(sut, place.events)

    def test_presence_should_sync_references(self):
        presence = Presence(Presence.Role.SUBJECT)
        sut = Event('1', Event.Type.BIRTH)
        sut.presences.add(presence)
        self.assertCountEqual([presence], sut.presences)
        self.assertEquals(sut, presence.event)
        sut.presences.remove(presence)
        self.assertCountEqual([], sut.presences)
        self.assertIsNone(presence.event)


class DateTest(TestCase):
    def test_year(self):
        year = 1970
        sut = Date(year=year)
        self.assertEquals(year, sut.year)

    def test_month(self):
        month = 1
        sut = Date(month=month)
        self.assertEquals(month, sut.month)

    def test_day(self):
        day = 1
        sut = Date(day=day)
        self.assertEquals(day, sut.day)

    @parameterized.expand([
        (True, 1970, 1, 1),
        (False, None, 1, 1),
        (False, 1970, None, 1),
        (False, 1970, 1, None),
        (False, None, None, 1),
        (False, 1970, None, None),
        (False, None, None, None),
    ])
    def test_complete(self, expected, year, month, day):
        sut = Date(year, month, day)
        self.assertEquals(expected, sut.complete)

    @parameterized.expand([
        (1970, 1, 1),
        (None, None, None),
    ])
    def test_parts(self, year, month, day):
        self.assertEquals((year, month, day), Date(year, month, day).parts)

    @parameterized.expand([
        (True, Date(1970, 1, 1)),
        (False, Date(1970, 1, None)),
        (False, Date(1970, None, 1)),
        (False, Date(None, 1, 1)),
        (False, Date(1970, None, None)),
        (False, Date(None, 1, None)),
        (False, Date(None, None, 1)),
        (False, None),
    ])
    def test_eq(self, expected, date):
        self.assertEquals(expected, date == Date(1970, 1, 1))

    @parameterized.expand([
        (True, 1970, 1, 2),
        (True, 1970, 2, 1),
        (True, 1971, 1, 1),
        (False, 1970, 1, 1),
        (False, 1970, 1, 1),
        (False, 1969, 1, 1),
        (False, 1969, 12, 12),
    ])
    def test_gt(self, expected, year, month, day):
        # This tests __lt__ and @total_ordering, by invoking the generated __gt__ implementation.
        sut = Date(year, month, day)
        self.assertEquals(expected, sut > Date(1970, 1, 1))

    @parameterized.expand([
        (Date(1970, 1, None),),
        (Date(1970, None, 1),),
        (Date(None, 1, 1),),
        (Date(1970, None, None),),
        (Date(None, 1, None),),
        (Date(None, None, 1),),
        (Date(None, None, None),),
        (None,),
    ])
    def test_gt_should_raise_typeerror_for_missing_parts(self, date):
        # This tests __lt__ and @total_ordering, by invoking the generated __gt__ implementation.
        with self.assertRaises(TypeError):
            date > Date(1970, 1, 1)


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
