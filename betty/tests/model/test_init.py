import pickle
from typing import Optional
from unittest.mock import Mock

from betty.model import EntityCollection, Entity, many_to_one, one_to_many, EventDispatchingEntityCollection, \
    many_to_many, many_to_one_to_many, GroupedEntityCollection
from betty.tests import TestCase


class EntityTest(TestCase):
    def test_id(self) -> None:
        entity_id = '000000001'
        sut = Entity(entity_id)
        self.assertEqual(entity_id, sut.id)


class EntityCollectionTest(TestCase):
    def test_pickle(self) -> None:
        sut = EntityCollection()
        pickle.dumps(sut)

    def test_prepend(self) -> None:
        sut = EntityCollection()
        entity1 = Entity('1')
        entity2 = Entity('2')
        entity3 = Entity('3')
        sut.prepend(entity3)
        sut.prepend(entity2)
        sut.prepend(entity1)
        # Prepend an already prepended value again, and assert that it was ignored.
        sut.prepend(entity1)
        self.assertIs(entity1, sut['1'])
        self.assertIs(entity2, sut['2'])
        self.assertIs(entity3, sut['3'])

    def test_append(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity3)
        sut.append(entity2)
        sut.append(entity1)
        # Append an already appended value again, and assert that it was ignored.
        sut.append(entity1)
        self.assertSequenceEqual([entity3, entity2, entity1], sut)

    def test_remove(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        entity4 = Entity()
        sut.append(entity1, entity2, entity3, entity4)
        sut.remove(entity4, entity2)
        self.assertSequenceEqual([entity1, entity3], sut)

    def test_replace(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        entity4 = Entity()
        entity5 = Entity()
        entity6 = Entity()
        sut.append(entity1, entity2, entity3)
        sut.replace(entity4, entity5, entity6)
        self.assertSequenceEqual([entity4, entity5, entity6], sut)

    def test_clear(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        sut.clear()
        self.assertSequenceEqual([], sut)

    def test_list(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertIs(entity1, sut[0])
        self.assertIs(entity2, sut[1])
        self.assertIs(entity3, sut[2])

    def test_len(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertEqual(3, len(sut))

    def test_iter(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertSequenceEqual([entity1, entity2, entity3], list(sut))

    def test_getitem(self) -> None:
        sut = EntityCollection()
        entity1 = Entity('1')
        entity2 = Entity('2')
        entity3 = Entity('3')
        sut.append(entity1, entity2, entity3)
        self.assertIs(entity1, sut[0])
        self.assertIs(entity1, sut['1'])
        self.assertIs(entity2, sut[1])
        self.assertIs(entity2, sut['2'])
        self.assertIs(entity3, sut[2])
        self.assertIs(entity3, sut['3'])
        self.assertSequenceEqual([entity1, entity2, entity3], sut[0:3])
        with self.assertRaises(KeyError):
            sut['4']

    def test_delitem(self) -> None:
        sut = EntityCollection()
        entity1 = Entity('1')
        entity2 = Entity('2')
        entity3 = Entity('3')
        sut.append(entity1, entity2, entity3)

        del sut['2']

        self.assertSequenceEqual([entity1, entity3], sut)
        with self.assertRaises(KeyError):
            sut['2']

    def test_contains(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        sut.append(entity1)

        self.assertIn(entity1, sut)
        self.assertNotIn(entity2, sut)

    def test_set_like_functionality(self) -> None:
        sut = EntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        entity4 = Entity()
        entity5 = Entity()
        entity6 = Entity()
        entity7 = Entity()
        entity8 = Entity()
        entity9 = Entity()
        # Ensure duplicates are skipped.
        sut.append(entity1, entity2, entity3, entity1, entity2, entity3, entity1, entity2, entity3)
        # Ensure skipped duplicates do not affect further new values.
        sut.append(entity1, entity2, entity3, entity4, entity5, entity6, entity7, entity8, entity9)
        self.assertSequenceEqual([entity1, entity2, entity3, entity4, entity5, entity6, entity7, entity8, entity9], sut)


class EventDispatchingEntityCollectionTest(TestCase):
    class _PickleableCallable:
        def __call__(self, *args, **kwargs):
            pass

    class _SelfReferentialHandler:
        def __init__(self, handled_self):
            self._handled_self = handled_self

    class _SelfReferentialOnAdd(_SelfReferentialHandler):
        def __call__(self, other_self):
            other_self.other_selfs.append(self._handled_self)

    class _SelfReferentialOnRemove(_SelfReferentialHandler):
        def __call__(self, other_self):
            other_self.other_selfs.remove(self._handled_self)

    class _SelfReferentialEntity(Entity):
        def __init__(self):
            super().__init__()
            self.other_selfs = EventDispatchingEntityCollection(
                EventDispatchingEntityCollectionTest._SelfReferentialOnAdd(self),
                EventDispatchingEntityCollectionTest._SelfReferentialOnRemove(self),
            )

    def test_pickle(self) -> None:
        sut = EventDispatchingEntityCollection(
            EventDispatchingEntityCollectionTest._PickleableCallable(),
            EventDispatchingEntityCollectionTest._PickleableCallable(),
        )
        pickle.dumps(sut)

    def test_pickle_with_recursion(self) -> None:
        entity1 = self._SelfReferentialEntity()
        entity2 = self._SelfReferentialEntity()
        entity1.other_selfs.append(entity2)
        self.assertIn(entity2, entity1.other_selfs)
        self.assertIn(entity1, entity2.other_selfs)
        pickle.dumps(entity1)
        pickle.dumps(entity2)

    def test_prepend(self) -> None:
        added = []
        on_remove = Mock()
        sut = EventDispatchingEntityCollection(lambda value: added.append(value), on_remove)
        entity1 = Entity('1')
        entity2 = Entity('2')
        entity3 = Entity('3')
        sut.prepend(entity3)
        sut.prepend(entity2)
        sut.prepend(entity1)
        # Prepend an already prepended value again, and assert that it was ignored.
        sut.prepend(entity1)
        self.assertIs(entity1, sut['1'])
        self.assertIs(entity2, sut['2'])
        self.assertIs(entity3, sut['3'])
        self.assertIs(entity3, added[0])
        self.assertIs(entity2, added[1])
        self.assertIs(entity1, added[2])
        on_remove.assert_not_called()

    def test_append(self) -> None:
        added = []
        on_remove = Mock()
        sut = EventDispatchingEntityCollection(lambda value: added.append(value), on_remove)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity3)
        sut.append(entity2)
        sut.append(entity1)
        # Append an already appended value again, and assert that it was ignored.
        sut.append(entity1)
        self.assertSequenceEqual([entity3, entity2, entity1], sut)
        self.assertSequenceEqual([entity3, entity2, entity1], added)
        on_remove.assert_not_called()

    def test_remove(self) -> None:
        added = []
        removed = []
        sut = EventDispatchingEntityCollection(lambda value: added.append(value), lambda value: removed.append(value))
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        entity4 = Entity()
        sut.append(entity1, entity2, entity3, entity4)
        sut.remove(entity4, entity2)
        self.assertSequenceEqual([entity1, entity3], sut)
        self.assertSequenceEqual([entity1, entity2, entity3, entity4], added)
        self.assertSequenceEqual([entity4, entity2], removed)

    def test_replace(self) -> None:
        added = []
        removed = []
        sut = EventDispatchingEntityCollection(lambda value: added.append(value), lambda value: removed.append(value))
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        entity4 = Entity()
        entity5 = Entity()
        entity6 = Entity()
        sut.append(entity1, entity2, entity3)
        sut.replace(entity4, entity5, entity6)
        self.assertSequenceEqual([entity4, entity5, entity6], sut)
        self.assertSequenceEqual([entity1, entity2, entity3, entity4, entity5, entity6], added)
        self.assertSequenceEqual([entity1, entity2, entity3], removed)

    def test_clear(self) -> None:
        added = []
        removed = []
        sut = EventDispatchingEntityCollection(lambda value: added.append(value), lambda value: removed.append(value))
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        sut.clear()
        self.assertSequenceEqual([], sut)
        self.assertIs(entity1, added[0])
        self.assertIs(entity2, added[1])
        self.assertIs(entity3, added[2])
        self.assertIs(entity1, removed[0])
        self.assertIs(entity2, removed[1])
        self.assertIs(entity3, removed[2])

    def test_list(self) -> None:
        sut = EventDispatchingEntityCollection(lambda _: None, lambda _: None)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertIs(entity1, sut[0])
        self.assertIs(entity2, sut[1])
        self.assertIs(entity3, sut[2])

    def test_delitem(self) -> None:
        added = []
        removed = []
        sut = EventDispatchingEntityCollection(lambda value: added.append(value), lambda value: removed.append(value))
        entity1 = Entity('1')
        entity2 = Entity('2')
        entity3 = Entity('3')
        sut.append(entity1, entity2, entity3)

        del sut['2']

        self.assertSequenceEqual([entity1, entity3], sut)
        with self.assertRaises(KeyError):
            sut['2']
        self.assertSequenceEqual([entity2], removed)


class GroupedEntityCollectionTest(TestCase):
    class _One(Entity):
        pass

    class _Other(Entity):
        pass

    def test_prepend(self) -> None:
        sut = GroupedEntityCollection()
        entity_one = self._One()
        entity_other1 = self._Other()
        entity_other2 = self._Other()
        entity_other3 = self._Other()
        sut.prepend(entity_one, entity_other1, entity_other2, entity_other3)
        self.assertSequenceEqual([entity_other3, entity_other2, entity_other1], sut[self._Other])

    def test_append(self) -> None:
        sut = GroupedEntityCollection()
        entity_one = self._One()
        entity_other1 = self._Other()
        entity_other2 = self._Other()
        entity_other3 = self._Other()
        sut.append(entity_one, entity_other1, entity_other2, entity_other3)
        self.assertSequenceEqual([entity_other1, entity_other2, entity_other3], sut[self._Other])

    def test_remove(self) -> None:
        sut = GroupedEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other)
        sut.remove(entity_one)
        self.assertSequenceEqual([entity_other], list(sut))
        sut.remove(entity_other)
        self.assertSequenceEqual([], list(sut))

    def test_getitem(self) -> None:
        sut = GroupedEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other)
        self.assertIs(entity_one, sut[0])
        self.assertIs(entity_other, sut[1])

    def test_iter(self) -> None:
        sut = GroupedEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other)
        self.assertSequenceEqual([entity_one, entity_other], list(sut))

    def test_len(self) -> None:
        sut = GroupedEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other)
        self.assertEqual(2, len(sut))

    def test_contain(self) -> None:
        sut = GroupedEntityCollection()
        entity_one = self._One()
        entity_other1 = self._Other()
        entity_other2 = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other1)
        self.assertIn(entity_one, sut)
        self.assertIn(entity_other1, sut)
        self.assertNotIn(entity_other2, sut)


class ManyToManyTest(TestCase):
    @many_to_many('other_many', 'many')
    class _Many(Entity):
        other_many: EntityCollection['ManyToManyTest._OtherMany']

    @many_to_many('many', 'other_many')
    class _OtherMany(Entity):
        many: EntityCollection['ManyToManyTest._Many']

    def test(self) -> None:
        entity_many = self._Many()
        entity_other_many = self._OtherMany()

        entity_many.other_many.append(entity_other_many)
        self.assertSequenceEqual([entity_other_many], entity_many.other_many)
        self.assertSequenceEqual([entity_many], entity_other_many.many)

        entity_many.other_many.remove(entity_other_many)
        self.assertSequenceEqual([], entity_many.other_many)
        self.assertSequenceEqual([], entity_other_many.many)

    def test_pickle(self) -> None:
        entity = self._Many()
        pickle.dumps(entity)


class ManyToOneToManyTest(TestCase):
    @many_to_one_to_many('one', 'left_many', 'right_many', 'one')
    class _One(Entity):
        left_many: Optional['ManyToOneToManyTest._Many']
        right_many: Optional['ManyToOneToManyTest._Many']

    @one_to_many('one', 'many')
    class _Many(Entity):
        one: EntityCollection['ManyToOneToManyTest._One']

    def test(self) -> None:
        entity_one = self._One()
        entity_left_many = self._Many()
        entity_right_many = self._Many()

        entity_one.left_many = entity_left_many
        self.assertIs(entity_left_many, entity_one.left_many)
        self.assertSequenceEqual([entity_one], entity_left_many.one)

        entity_one.right_many = entity_right_many
        self.assertIs(entity_right_many, entity_one.right_many)
        self.assertSequenceEqual([entity_one], entity_right_many.one)

        del entity_one.left_many
        self.assertIsNone(entity_one.left_many)
        self.assertSequenceEqual([], entity_left_many.one)
        self.assertIsNone(entity_one.right_many)
        self.assertSequenceEqual([], entity_right_many.one)

    def test_pickle(self) -> None:
        entity = self._One()
        pickle.dumps(entity)


class OneToManyTest(TestCase):
    @one_to_many('many', 'one')
    class _One(Entity):
        many: EntityCollection['OneToManyTest._Many']

    @many_to_one('one', 'many')
    class _Many(Entity):
        one: Optional['OneToManyTest._One']

    def test(self) -> None:
        entity_one = self._One()
        entity_many = self._Many()

        entity_one.many.append(entity_many)
        self.assertSequenceEqual([entity_many], entity_one.many)
        self.assertIs(entity_one, entity_many.one)

        entity_one.many.remove(entity_many)
        self.assertSequenceEqual([], entity_one.many)
        self.assertIsNone(entity_many.one)

    def test_pickle(self) -> None:
        entity = self._One()
        pickle.dumps(entity)


class ManyToOneTest(TestCase):
    @many_to_one('one', 'many')
    class _Many(Entity):
        one: Optional['ManyToOneTest._One']

    @one_to_many('many', 'one')
    class _One(Entity):
        many: EntityCollection['ManyToOneTest._Many']

    def test(self) -> None:
        entity_many = self._Many()
        entity_one = self._One()

        entity_many.one = entity_one
        self.assertIs(entity_one, entity_many.one)
        self.assertSequenceEqual([entity_many], entity_one.many)

        del entity_many.one
        self.assertIsNone(entity_many.one)
        self.assertSequenceEqual([], entity_one.many)

    def test_pickle(self) -> None:
        entity = self._Many()
        pickle.dumps(entity)
