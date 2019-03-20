from unittest import TestCase

from betty.ancestry import EventHandlingSet, Person, Family


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
        self.assertEquals([value], list(sut))
        self.assertEquals([value], reference)
        sut.remove(value)
        self.assertEquals([], list(sut))
        self.assertEquals([], reference)

    def test_without_handler(self):
        sut = EventHandlingSet()
        value = 'A valuable value'
        sut.add(value)
        self.assertEquals([value], list(sut))
        sut.remove(value)
        self.assertEquals([], list(sut))


class PersonTest(TestCase):
    def test_ancestor_families_should_sync_references(self):
        family = Family('1')
        sut = Person('1')
        sut.ancestor_families.add(family)
        self.assertEquals([family], list(sut.ancestor_families))
        self.assertEquals([sut], list(family.parents))
        sut.ancestor_families.remove(family)
        self.assertEquals([], list(sut.ancestor_families))
        self.assertEqual([], list(family.parents))

    def test_descendant_family_should_sync_references(self):
        family = Family('1')
        sut = Person('1')
        sut.descendant_family = family
        self.assertEquals(family, sut.descendant_family)
        self.assertEquals([sut], list(family.children))
        sut.descendant_family = None
        self.assertIsNone(sut.descendant_family)
        self.assertEquals([], list(family.children))

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

    def test_children_without_descendant_family(self):
        sut = Person('person')
        self.assertEquals([], sut.parents)

    def test_children_with_descendant_family(self):
        parent_1 = Person('1')
        parent_2 = Person('2')
        family = Family('1')
        family.parents = [parent_1, parent_2]

        sut = Person('person')
        sut.descendant_family = family

        self.assertCountEqual([parent_1, parent_2], sut.parents)


class FamilyTest(TestCase):
    def test_parents_should_sync_references(self):
        parent = Person('1')
        sut = Family('1')
        sut.parents.add(parent)
        self.assertEquals([parent], list(sut.parents))
        self.assertEquals([sut], list(parent.ancestor_families))
        sut.parents.remove(parent)
        self.assertEquals([], list(sut.parents))
        self.assertEquals([], list(parent.ancestor_families))

    def test_children_should_sync_references(self):
        child = Person('1')
        sut = Family('1')
        sut.children.add(child)
        self.assertEquals([child], list(sut.children))
        self.assertEquals(sut, child.descendant_family)
        sut.children.remove(child)
        self.assertEquals([], list(sut.children))
        self.assertEquals(None, child.descendant_family)
