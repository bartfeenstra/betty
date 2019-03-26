from tempfile import TemporaryFile, NamedTemporaryFile
from unittest import TestCase
from unittest.mock import Mock

from parameterized import parameterized

from betty.ancestry import EventHandlingSet, Person, Family, Event, Place, Date, File, Note, Document


class EventHandlingSetTest(TestCase):
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
        sut.remove(value)
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
    def test_ancestor_families_should_sync_references(self):
        family = Family('1')
        sut = Person('1')
        sut.ancestor_families.add(family)
        self.assertCountEqual([family], sut.ancestor_families)
        self.assertCountEqual([sut], family.parents)
        sut.ancestor_families.remove(family)
        self.assertCountEqual([], sut.ancestor_families)
        self.assertCountEqual([], family.parents)

    def test_descendant_family_should_sync_references(self):
        family = Family('1')
        sut = Person('1')
        sut.descendant_family = family
        self.assertEquals(family, sut.descendant_family)
        self.assertCountEqual([sut], family.children)
        sut.descendant_family = None
        self.assertIsNone(sut.descendant_family)
        self.assertCountEqual([], family.children)

    def test_children_without_ancestor_families(self):
        sut = Person('person')
        self.assertEquals([], sut.children)

    def test_children_with_multiple_ancestor_families(self):
        child_1_1 = Person('1_1')
        child_1_2 = Person('1_2')
        family_1 = Family('1')
        family_1.children = [child_1_1, child_1_2]

        child_2_1 = Person('2_1')
        child_2_2 = Person('2_2')
        family_2 = Family('2')
        family_2.children = [child_2_1, child_2_2]

        sut = Person('person')
        sut.ancestor_families = [family_1, family_2]

        self.assertCountEqual(
            [child_1_1, child_1_2, child_2_1, child_2_2], sut.children)

    def test_parents_without_descendant_family(self):
        sut = Person('person')
        self.assertEquals([], sut.parents)

    def test_parents_with_descendant_family(self):
        parent_1 = Mock(Person)
        parent_2 = Mock(Person)
        family = Family('1')
        family.parents = [parent_1, parent_2]

        sut = Person('person')
        sut.descendant_family = family

        self.assertCountEqual([parent_1, parent_2], sut.parents)

    def test_siblings_without_descendant_family(self):
        sut = Person('person')
        self.assertCountEqual([], sut.siblings)

    def test_siblings_with_descendant_families(self):
        parent = Person('1')
        sibling = Mock(Person)
        descendant_family = Family('1')
        descendant_family.parents.add(parent)
        descendant_family.children.add(sibling)

        half_family = Family('1')
        half_sibling = Mock(Person)
        half_family.parents.add(parent)
        half_family.children.add(half_sibling)

        sut = Person('person')
        sut.descendant_family = descendant_family

        self.assertCountEqual([sibling, half_sibling], sut.siblings)

    def test_events(self):
        sut = Person('1')
        self.assertCountEqual([], sut.events)
        events = (Mock(Event), Mock(Event))
        sut.events = events
        self.assertCountEqual(events, sut.events)

    def test_events_should_sync_references(self):
        event = Event('1', Event.Type.BIRTH)
        sut = Person('1')
        sut.events.add(event)
        self.assertCountEqual([event], sut.events)
        self.assertCountEqual([sut], event.people)
        sut.events.remove(event)
        self.assertCountEqual([], sut.events)
        self.assertCountEqual([], event.people)


class FamilyTest(TestCase):
    def test_parents_should_sync_references(self):
        parent = Person('1')
        sut = Family('1')
        sut.parents.add(parent)
        self.assertCountEqual([parent], sut.parents)
        self.assertCountEqual([sut], parent.ancestor_families)
        sut.parents.remove(parent)
        self.assertCountEqual([], sut.parents)
        self.assertCountEqual([], parent.ancestor_families)

    def test_children_should_sync_references(self):
        child = Person('1')
        sut = Family('1')
        sut.children.add(child)
        self.assertCountEqual([child], sut.children)
        self.assertEquals(sut, child.descendant_family)
        sut.children.remove(child)
        self.assertCountEqual([], sut.children)
        self.assertEquals(None, child.descendant_family)


class PlaceTest(TestCase):
    def test_events_should_sync_references(self):
        sut = Place('1')
        event = Event('1', Event.Type.BIRTH)
        sut.events.add(event)
        self.assertIn(event, sut.events)
        self.assertEquals(sut, event.place)
        sut.events.remove(event)
        self.assertCountEqual([], sut.events)
        self.assertEquals(None, event.place)

    def test_encloses_should_sync_references(self):
        sut = Place('1')
        enclosed_place = Place('2')
        sut.encloses.add(enclosed_place)
        self.assertIn(enclosed_place, sut.encloses)
        self.assertEquals(sut, enclosed_place.enclosed_by)
        sut.encloses.remove(enclosed_place)
        self.assertCountEqual([], sut.encloses)
        self.assertEquals(None, enclosed_place.enclosed_by)

    def test_enclosed_by_should_sync_references(self):
        sut = Place('1')
        enclosing_place = Place('2')
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

    def test_label_with_type_only(self):
        event_type = Event.Type.BIRTH
        sut = Event('1', event_type)
        self.assertEquals('Birth', sut.label)

    def test_label_with_people(self):
        event_type = Event.Type.MARRIAGE
        sut = Event('1', event_type)
        people = [
            Person('1', 'Jane', 'Doe'),
            Person('2', 'Janet', 'Dough'),
        ]
        sut.people = people
        self.assertEquals('Marriage of Doe, Jane and Dough, Janet', sut.label)

    def test_place_should_sync_references(self):
        place = Place('1')
        sut = Event('1', Event.Type.BIRTH)
        sut.place = place
        self.assertEquals(place, sut.place)
        self.assertIn(sut, place.events)
        sut.place = None
        self.assertEquals(None, sut.place)
        self.assertNotIn(sut, place.events)

    def test_people_should_sync_references(self):
        person = Person('1')
        sut = Event('1', Event.Type.BIRTH)
        sut.people.add(person)
        self.assertCountEqual([person], sut.people)
        self.assertCountEqual([sut], person.events)
        sut.people.remove(person)
        self.assertCountEqual([], sut.people)
        self.assertCountEqual([], person.events)


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


class FileTest(TestCase):
    def test_path(self):
        with TemporaryFile() as f:
            sut = File(f.name)
            self.assertEquals(f.name, sut.path)

    def test_extension_with_extension(self):
        extension = 'betty'
        with NamedTemporaryFile(suffix='.%s' % extension) as f:
            sut = File(f.name)
            self.assertEquals(extension, sut.extension)

    def test_extension_without_extension(self):
        with NamedTemporaryFile() as f:
            sut = File(f.name)
            self.assertIsNone(sut.extension)


class NoteTest(TestCase):
    def test_text(self):
        text = 'Betty wrote this.'
        sut = Note(text)
        self.assertEquals(text, sut.text)


class DocumentTest(TestCase):
    def test_id(self):
        entity_id = 'BETTY01'
        file = Mock(File)
        sut = Document(entity_id, file)
        self.assertEquals(entity_id, sut.id)

    def test_file(self):
        entity_id = 'BETTY01'
        file = Mock(File)
        sut = Document(entity_id, file)
        self.assertEquals(file, sut.file)

    def test_description(self):
        entity_id = 'BETTY01'
        file = Mock(File)
        sut = Document(entity_id, file)
        description = 'Hi, my name is Betty!'
        sut.description = description
        self.assertEquals(description, sut.description)

    def test_label_with_description(self):
        entity_id = 'BETTY01'
        file = Mock(File)
        sut = Document(entity_id, file)
        description = 'Hi, my name is Betty!'
        sut.description = description
        self.assertEquals(description, sut.label)

    def test_label_without_description(self):
        entity_id = 'BETTY01'
        file = Mock(File)
        sut = Document(entity_id, file)
        self.assertIsInstance(sut.label, str)

    def test_notes(self):
        entity_id = 'BETTY01'
        file = Mock(File)
        sut = Document(entity_id, file)
        self.assertCountEqual([], sut.notes)
        notes = (Mock(Note), Mock(Note))
        sut.notes = notes
        self.assertCountEqual(notes, sut.notes)
