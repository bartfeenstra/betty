from __future__ import annotations

import copy
import pickle
from typing import Optional, Any

from parameterized import parameterized

from betty.model import GeneratedEntityId, get_entity_type_name, Entity, get_entity_type, _EntityTypeAssociation, \
    _EntityTypeAssociationRegistry, SingleTypeEntityCollection, _AssociateCollection, EntityT, \
    MultipleTypesEntityCollection, one_to_many, many_to_one_to_many, FlattenedEntityCollection, many_to_many, \
    EntityCollection, to_many, many_to_one, to_one, one_to_one
from betty.model.ancestry import Person
from betty.tests import TestCase


class _OtherEntity(Entity):
    pass


class GeneratedEntityidTest(TestCase):
    def test_pickle(self) -> None:
        sut = GeneratedEntityId()
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        self.assertEqual(sut, unpickled_sut)

    def test_copy(self) -> None:
        sut = GeneratedEntityId()
        copied_sut = copy.copy(sut)
        self.assertEqual(sut, copied_sut)

    def test_deepcopy(self) -> None:
        sut = GeneratedEntityId()
        copied_sut = copy.deepcopy(sut)
        self.assertEqual(sut, copied_sut)


class EntityTest(TestCase):
    def test_id(self) -> None:
        entity_id = '000000001'
        sut = Entity(entity_id)
        self.assertEqual(entity_id, sut.id)

    def test_entity_type_with_class(self) -> None:
        self.assertEqual(Entity, Entity.entity_type())

    def test_entity_type_with_instance(self) -> None:
        self.assertEqual(Entity, Entity().entity_type())


class GetEntityTypeNameTest(TestCase):
    def test_with_betty_entity(self) -> None:
        self.assertEqual('Person', get_entity_type_name(Person))

    def test_with_other_entity(self) -> None:
        self.assertEqual('betty.tests.model.test___init__._OtherEntity', get_entity_type_name(_OtherEntity))


class GetEntityTypeTest(TestCase):
    def test_with_betty_entity(self) -> None:
        self.assertEqual(Person, get_entity_type('Person'))

    def test_with_other_entity(self) -> None:
        self.assertEqual(_OtherEntity, get_entity_type('betty.tests.model.test___init__._OtherEntity'))

    def test_with_unknown_entity(self) -> None:
        with self.assertRaises(ValueError):
            get_entity_type('betty_non_existent.UnknownEntity')


class _EntityTypeAssociationRegistryTest(TestCase):
    class _ParentEntity(Entity):
        pass

    class _ChildEntity(_ParentEntity):
        pass

    _parent_registration = None
    _child_registration = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._parent_registration = _EntityTypeAssociation(cls._ParentEntity, 'parent_associate', _EntityTypeAssociation.Cardinality.ONE)
        _EntityTypeAssociationRegistry.register(cls._parent_registration)
        cls._child_registration = _EntityTypeAssociation(cls._ChildEntity, 'child_associate', _EntityTypeAssociation.Cardinality.MANY)
        _EntityTypeAssociationRegistry.register(cls._child_registration)

    @classmethod
    def tearDownClass(cls) -> None:
        _EntityTypeAssociationRegistry._registrations.remove(cls._parent_registration)
        _EntityTypeAssociationRegistry._registrations.remove(cls._child_registration)

    def test_get_associations_with_parent_class_should_return_parent_associations(self) -> None:
        self.assertSetEqual({self._parent_registration}, _EntityTypeAssociationRegistry.get_associations(self._ParentEntity))

    def test_get_associations_with_child_class_should_return_child_associations(self) -> None:
        self.assertSetEqual({self._parent_registration, self._child_registration}, _EntityTypeAssociationRegistry.get_associations(self._ChildEntity))


class SingleTypeEntityCollectionTest(TestCase):
    def test_pickle(self) -> None:
        entity = Entity()
        sut = SingleTypeEntityCollection(Entity)
        sut.append(entity)
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        self.assertEqual(1, len(unpickled_sut))
        self.assertEqual(entity.id, unpickled_sut[0].id)

    def test_copy(self) -> None:
        entity = Entity()
        sut = SingleTypeEntityCollection(Entity)
        sut.append(entity)
        copied_sut = copy.copy(sut)
        self.assertEqual(1, len(copied_sut))
        self.assertEqual(entity.id, copied_sut[0].id)

    def test_deepcopy(self) -> None:
        entity = Entity()
        sut = SingleTypeEntityCollection(Entity)
        sut.append(entity)
        copied_sut = copy.deepcopy(sut)
        self.assertEqual(1, len(copied_sut))
        self.assertEqual(entity.id, copied_sut[0].id)

    def test_prepend(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
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
        sut = SingleTypeEntityCollection(Entity)
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
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        entity4 = Entity()
        sut.append(entity1, entity2, entity3, entity4)
        sut.remove(entity4, entity2)
        self.assertSequenceEqual([entity1, entity3], sut)

    def test_replace(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
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
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        sut.clear()
        self.assertSequenceEqual([], sut)

    def test_list(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertIs(entity1, sut[0])
        self.assertIs(entity2, sut[1])
        self.assertIs(entity3, sut[2])

    def test_len(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertEqual(3, len(sut))

    def test_iter(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertSequenceEqual([entity1, entity2, entity3], list(sut))

    def test_getitem_by_index(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertIs(entity1, sut[0])
        self.assertIs(entity2, sut[1])
        self.assertIs(entity3, sut[2])
        with self.assertRaises(IndexError):
            sut[3]

    def test_getitem_by_indices(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)
        self.assertSequenceEqual([entity1, entity3], sut[0::2])

    def test_getitem_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity('1')
        entity2 = Entity('2')
        entity3 = Entity('3')
        sut.append(entity1, entity2, entity3)
        self.assertIs(entity1, sut['1'])
        self.assertIs(entity2, sut['2'])
        self.assertIs(entity3, sut['3'])
        with self.assertRaises(KeyError):
            sut['4']

    def test_delitem_by_index(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)

        del sut[1]

        self.assertSequenceEqual([entity1, entity3], sut)

    def test_delitem_by_indices(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)

        del sut[0::2]

        self.assertSequenceEqual([entity2], sut)

    def test_delitem_by_entity(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)

        del sut[entity2]

        self.assertSequenceEqual([entity1, entity3], sut)

    def test_delitem_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity('1')
        entity2 = Entity('2')
        entity3 = Entity('3')
        sut.append(entity1, entity2, entity3)

        del sut['2']

        self.assertSequenceEqual([entity1, entity3], sut)

    def test_contains_by_entity(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        sut.append(entity1)

        self.assertIn(entity1, sut)
        self.assertNotIn(entity2, sut)

    def test_contains_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        sut.append(entity1)

        self.assertIn(entity1.id, sut)
        self.assertNotIn(entity2.id, sut)

    @parameterized.expand([
        (True,),
        (False,),
        ([],),
    ])
    def test_contains_by_unsupported_typed(self, value: Any) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity = Entity()
        sut.append(entity)

        self.assertNotIn(value, sut)

    def test_set_like_functionality(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
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

    def test_add(self) -> None:
        sut1 = SingleTypeEntityCollection(Entity)
        sut2 = SingleTypeEntityCollection(Entity)
        entity1 = Entity()
        entity2 = Entity()
        sut1.append(entity1)
        sut2.append(entity2)
        sut_added = sut1 + sut2
        self.assertIsInstance(sut_added, SingleTypeEntityCollection)
        self.assertSequenceEqual([entity1, entity2], sut_added)


class AssociateCollectionTest(TestCase):
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
        def __init__(self, entity_id: Optional[str] = None):
            super().__init__(entity_id)
            self.other_selfs = AssociateCollectionTest._TrackingAssociateCollection(self)

    class _TrackingAssociateCollection(_AssociateCollection):
        def __init__(self, owner: AssociateCollectionTest._SelfReferentialEntity):
            super().__init__(owner, AssociateCollectionTest._SelfReferentialEntity)
            self.added = []
            self.removed = []

        def _on_add(self, associate: EntityT) -> None:
            self.added.append(associate)

        def _on_remove(self, associate: EntityT) -> None:
            self.removed.append(associate)

    class _NoOpAssociateCollection(_AssociateCollection):
        def __init__(self, owner: AssociateCollectionTest._SelfReferentialEntity):
            super().__init__(owner, AssociateCollectionTest._SelfReferentialEntity)

        def _on_add(self, associate: EntityT) -> None:
            pass

        def _on_remove(self, associate: EntityT) -> None:
            pass

    def test_pickle(self) -> None:
        owner = self._SelfReferentialEntity()
        associate = self._SelfReferentialEntity()
        sut = self._NoOpAssociateCollection(owner)
        sut.append(associate)
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        self.assertEqual(1, len(unpickled_sut))
        self.assertEqual(associate.id, unpickled_sut[0].id)

    def test_copy(self) -> None:
        owner = self._SelfReferentialEntity()
        associate = self._SelfReferentialEntity()
        sut = self._NoOpAssociateCollection(owner)
        sut.append(associate)
        copied_sut = copy.copy(sut)
        self.assertEqual(1, len(copied_sut))
        self.assertEqual(associate.id, copied_sut[0].id)

    def test_deepcopy(self) -> None:
        owner = self._SelfReferentialEntity()
        associate = self._SelfReferentialEntity()
        sut = self._NoOpAssociateCollection(owner)
        sut.append(associate)
        copied_sut = copy.deepcopy(sut)
        self.assertEqual(1, len(copied_sut))
        self.assertEqual(associate.id, copied_sut[0].id)

    def test_pickle_with_recursion(self) -> None:
        owner = self._SelfReferentialEntity()
        associate = self._SelfReferentialEntity()
        owner.other_selfs.append(associate)
        pickle.dumps(owner)
        pickle.dumps(associate)

    def test_prepend(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity('1')
        associate2 = self._SelfReferentialEntity('2')
        associate3 = self._SelfReferentialEntity('3')
        sut.prepend(associate3)
        sut.prepend(associate2)
        sut.prepend(associate1)
        # Prepend an already prepended value again, and assert that it was ignored.
        sut.prepend(associate1)
        self.assertIs(associate1, sut['1'])
        self.assertIs(associate2, sut['2'])
        self.assertIs(associate3, sut['3'])
        self.assertIs(associate3, sut.added[0])
        self.assertIs(associate2, sut.added[1])
        self.assertIs(associate1, sut.added[2])
        self.assertSequenceEqual([], sut.removed)

    def test_append(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate3)
        sut.append(associate2)
        sut.append(associate1)
        # Append an already appended value again, and assert that it was ignored.
        sut.append(associate1)
        self.assertSequenceEqual([associate3, associate2, associate1], sut)
        self.assertSequenceEqual([associate3, associate2, associate1], sut.added)
        self.assertSequenceEqual([], sut.removed)

    def test_remove(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        associate4 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3, associate4)
        sut.remove(associate4, associate2)
        self.assertSequenceEqual([associate1, associate3], sut)
        self.assertSequenceEqual([associate1, associate2, associate3, associate4], sut.added)
        self.assertSequenceEqual([associate4, associate2], sut.removed)

    def test_replace(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        associate4 = self._SelfReferentialEntity()
        associate5 = self._SelfReferentialEntity()
        associate6 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)
        sut.replace(associate4, associate5, associate6)
        self.assertSequenceEqual([associate4, associate5, associate6], sut)
        self.assertSequenceEqual([associate1, associate2, associate3, associate4, associate5, associate6], sut.added)
        self.assertSequenceEqual([associate1, associate2, associate3], sut.removed)

    def test_clear(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)
        sut.clear()
        self.assertSequenceEqual([], sut)
        self.assertIs(associate1, sut.added[0])
        self.assertIs(associate2, sut.added[1])
        self.assertIs(associate3, sut.added[2])
        self.assertIs(associate1, sut.removed[0])
        self.assertIs(associate2, sut.removed[1])
        self.assertIs(associate3, sut.removed[2])

    def test_list(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)
        self.assertIs(associate1, sut[0])
        self.assertIs(associate2, sut[1])
        self.assertIs(associate3, sut[2])

    def test_delitem_by_index(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)

        del sut[1]

        self.assertSequenceEqual([associate1, associate3], sut)
        self.assertSequenceEqual([associate2], sut.removed)

    def test_delitem_by_indices(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)

        del sut[0::2]

        self.assertSequenceEqual([associate2], sut)
        self.assertSequenceEqual([associate1, associate3], sut.removed)

    def test_delitem_by_entity(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)

        del sut[associate2]

        self.assertSequenceEqual([associate1, associate3], sut)
        self.assertSequenceEqual([associate2], sut.removed)

    def test_delitem_by_entity_id(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity('1')
        associate2 = self._SelfReferentialEntity('2')
        associate3 = self._SelfReferentialEntity('3')
        sut.append(associate1, associate2, associate3)

        del sut['2']

        self.assertSequenceEqual([associate1, associate3], sut)
        self.assertSequenceEqual([associate2], sut.removed)


class MultipleTypesEntityCollectionTest(TestCase):
    class _One(Entity):
        pass

    class _Other(Entity):
        pass

    def test_pickle(self) -> None:
        entity_one = self._One()
        entity_other = self._Other()
        sut = MultipleTypesEntityCollection()
        sut.append(entity_one, entity_other)
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        self.assertEqual(2, len(unpickled_sut))
        self.assertEqual(1, len(unpickled_sut[self._One]))
        self.assertEqual(1, len(unpickled_sut[self._Other]))
        self.assertEqual(entity_one.id, unpickled_sut[self._One][0].id)
        self.assertEqual(entity_other.id, unpickled_sut[self._Other][0].id)

    def test_copy(self) -> None:
        entity_one = self._One()
        entity_other = self._Other()
        sut = MultipleTypesEntityCollection()
        sut.append(entity_one, entity_other)
        copied_sut = copy.copy(sut)
        self.assertEqual(2, len(copied_sut))
        self.assertEqual(1, len(copied_sut[self._One]))
        self.assertEqual(1, len(copied_sut[self._Other]))
        self.assertEqual(entity_one.id, copied_sut[self._One][0].id)
        self.assertEqual(entity_other.id, copied_sut[self._Other][0].id)

    def test_deepcopy(self) -> None:
        entity_one = self._One()
        entity_other = self._Other()
        sut = MultipleTypesEntityCollection()
        sut.append(entity_one, entity_other)
        copied_sut = copy.deepcopy(sut)
        self.assertEqual(2, len(copied_sut))
        self.assertEqual(1, len(copied_sut[self._One]))
        self.assertEqual(1, len(copied_sut[self._Other]))
        self.assertEqual(entity_one.id, copied_sut[self._One][0].id)
        self.assertEqual(entity_other.id, copied_sut[self._Other][0].id)

    def test_prepend(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other1 = self._Other()
        entity_other2 = self._Other()
        entity_other3 = self._Other()
        sut.prepend(entity_one, entity_other1, entity_other2, entity_other3)
        self.assertSequenceEqual([entity_other3, entity_other2, entity_other1], sut[self._Other])

    def test_append(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other1 = self._Other()
        entity_other2 = self._Other()
        entity_other3 = self._Other()
        sut.append(entity_one, entity_other1, entity_other2, entity_other3)
        self.assertSequenceEqual([entity_other1, entity_other2, entity_other3], sut[self._Other])

    def test_remove(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other)
        sut.remove(entity_one)
        self.assertSequenceEqual([entity_other], list(sut))
        sut.remove(entity_other)
        self.assertSequenceEqual([], list(sut))

    def test_getitem_by_index(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut.append(entity_one, entity_other)
        self.assertIs(entity_one, sut[0])
        self.assertIs(entity_other, sut[1])
        with self.assertRaises(IndexError):
            sut[2]

    def test_getitem_by_indices(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut.append(entity_one, entity_other)
        self.assertSequenceEqual([entity_one], sut[0:1:1])
        self.assertSequenceEqual([entity_other], sut[1::1])

    def test_getitem_by_entity_type(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut.append(entity_one, entity_other)
        self.assertSequenceEqual([entity_one], sut[self._One])
        self.assertSequenceEqual([entity_other], sut[self._Other])
        # Ensure that getting previously unseen entity types automatically creates and returns a new collection.
        self.assertSequenceEqual([], sut[Entity])

    def test_getitem_by_entity_type_name(self) -> None:
        sut = MultipleTypesEntityCollection()
        # Use an existing ancestry entity type, because converting an entity type name to an entity type only works for
        # entity types in a single module namespace.
        entity = Person(None)
        sut.append(entity)
        self.assertSequenceEqual([entity], sut['Person'])
        # Ensure that getting previously unseen entity types automatically creates and returns a new collection.
        with self.assertRaises(ValueError):
            sut['NonExistentEntityType']

    def test_delitem_by_index(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)

        del sut[1]

        self.assertSequenceEqual([entity1, entity3], sut)

    def test_delitem_by_indices(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)

        del sut[0::2]

        self.assertSequenceEqual([entity2], sut)

    def test_delitem_by_entity(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity1 = Entity()
        entity2 = Entity()
        entity3 = Entity()
        sut.append(entity1, entity2, entity3)

        del sut[entity2]

        self.assertSequenceEqual([entity1, entity3], sut)

    def test_delitem_by_entity_type(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity = Entity()
        entity_other = _OtherEntity()
        sut.append(entity, entity_other)

        del sut[Entity.entity_type()]

        self.assertSequenceEqual([entity_other], sut)

    def test_delitem_by_entity_type_name(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity = Entity()
        entity_other = _OtherEntity()
        sut.append(entity, entity_other)

        del sut[get_entity_type_name(Entity.entity_type())]

        self.assertSequenceEqual([entity_other], sut)

    def test_iter(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other)
        self.assertSequenceEqual([entity_one, entity_other], list(sut))

    def test_len(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other)
        self.assertEqual(2, len(sut))

    def test_contain_by_entity(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = self._One()
        entity_other1 = self._Other()
        entity_other2 = self._Other()
        sut[self._One].append(entity_one)
        sut[self._Other].append(entity_other1)
        self.assertIn(entity_one, sut)
        self.assertIn(entity_other1, sut)
        self.assertNotIn(entity_other2, sut)

    @parameterized.expand([
        (True,),
        (False,),
        ([],),
    ])
    def test_contains_by_unsupported_typed(self, value: Any) -> None:
        sut = MultipleTypesEntityCollection()
        entity = Entity()
        sut.append(entity)

        self.assertNotIn(value, sut)

    def test_add(self) -> None:
        sut1 = MultipleTypesEntityCollection()
        sut2 = MultipleTypesEntityCollection()
        entity1_one = self._One()
        entity1_other = self._One()
        entity2_one = self._Other()
        entity2_other = self._Other()
        sut1.append(entity1_one, entity1_other)
        sut2.append(entity2_one, entity2_other)
        sut_added = sut1 + sut2
        self.assertIsInstance(sut_added, MultipleTypesEntityCollection)
        self.assertSequenceEqual([entity1_one, entity1_other, entity2_one, entity2_other], sut_added)


class FlattenedEntityCollectionTest(TestCase):
    @many_to_many('other_many', 'many')
    class _ManyToMany_Many(Entity):
        other_many: EntityCollection[FlattenedEntityCollectionTest._ManyToMany_OtherMany]

    @many_to_many('many', 'other_many')
    class _ManyToMany_OtherMany(Entity):
        many: EntityCollection[FlattenedEntityCollectionTest._ManyToMany_Many]

    @one_to_many('other_many', 'many')
    class _ManyToOneToMany_Many(Entity):
        other_many: FlattenedEntityCollectionTest._ManyToOneToMany_OtherMany

    @many_to_one_to_many('other_many', 'many', 'other_many', 'many')
    class _ManyToOneToMany_One(Entity):
        many: FlattenedEntityCollectionTest._ManyToOneToMany_Many
        other_many: FlattenedEntityCollectionTest._ManyToOneToMany_OtherMany

    @one_to_many('many', 'other_many')
    class _ManyToOneToMany_OtherMany(Entity):
        many: FlattenedEntityCollectionTest._ManyToOneToMany_Many

    def test_add_to_many_association_then_unflatten(self) -> None:
        entity_many = self._ManyToMany_Many()
        entity_other_many = self._ManyToMany_OtherMany()

        flattened_entities = FlattenedEntityCollection()
        flattened_entities.add_entity(entity_many, entity_other_many)
        flattened_entities.add_association(self._ManyToMany_Many, entity_many.id, 'other_many', self._ManyToMany_OtherMany, entity_other_many.id)

        # Assert the result is pickleable.
        pickle.dumps(flattened_entities)

        unflattened_entities = flattened_entities.unflatten()

        unflattened_entity_many = unflattened_entities[self._ManyToMany_Many][0]
        unflattened_entity_other_many = unflattened_entities[self._ManyToMany_OtherMany][0]
        self.assertIsNot(entity_many, unflattened_entity_many)
        self.assertIsNot(entity_other_many, unflattened_entity_other_many)
        self.assertEqual(1, len(unflattened_entity_other_many.many))
        self.assertIn(unflattened_entity_many, unflattened_entity_other_many.many)
        self.assertEqual(1, len(unflattened_entity_many.other_many))
        self.assertIn(unflattened_entity_other_many, unflattened_entity_many.other_many)

    def test_add_entity_with_to_many_association_then_unflatten(self) -> None:
        entity_many = self._ManyToMany_Many()
        entity_other_many = self._ManyToMany_OtherMany()
        entity_many.other_many.append(entity_other_many)

        flattened_entities = FlattenedEntityCollection()
        flattened_entities.add_entity(entity_many, entity_other_many)

        # Assert the original entities remain unchanged.
        self.assertIn(entity_many, entity_other_many.many)
        self.assertIn(entity_other_many, entity_many.other_many)
        # Assert the result is pickleable.
        pickle.dumps(flattened_entities)

        unflattened_entities = flattened_entities.unflatten()

        unflattened_entity_many = unflattened_entities[self._ManyToMany_Many][0]
        unflattened_entity_other_many = unflattened_entities[self._ManyToMany_OtherMany][0]
        self.assertIsNot(entity_many, unflattened_entity_many)
        self.assertIsNot(entity_other_many, unflattened_entity_other_many)
        self.assertIn(unflattened_entity_many, unflattened_entity_other_many.many)
        self.assertIn(unflattened_entity_other_many, unflattened_entity_many.other_many)

    def test_add_entity_with_many_to_one_to_many_association_then_unflatten(self) -> None:
        entity_many = self._ManyToOneToMany_Many()
        entity_one = self._ManyToOneToMany_One()
        entity_other_many = self._ManyToOneToMany_OtherMany()
        entity_one.many = entity_many
        entity_one.other_many = entity_other_many

        flattened_entities = FlattenedEntityCollection()
        flattened_entities.add_entity(entity_many, entity_one, entity_other_many)

        # Assert the original entities remain unchanged.
        self.assertIs(entity_many, entity_one.many)
        self.assertIs(entity_other_many, entity_one.other_many)
        # Assert the result is pickleable.
        pickle.dumps(flattened_entities)

        unflattened_entity_many, unflattened_entity_one, unflattened_entity_other_many = flattened_entities.unflatten()

        self.assertIsNot(entity_many, unflattened_entity_many)
        self.assertIsNot(entity_other_many, unflattened_entity_other_many)
        self.assertIn(unflattened_entity_one, unflattened_entity_other_many.many)
        self.assertIn(unflattened_entity_one, unflattened_entity_many.other_many)
        self.assertIs(unflattened_entity_many, unflattened_entity_one.many)
        self.assertIs(unflattened_entity_other_many, unflattened_entity_one.other_many)


class ToOneTest(TestCase):
    @to_one('one')
    class _Some(Entity):
        one: Optional[ManyToOneTest._One]

    class _One(Entity):
        pass

    def test(self) -> None:
        self.assertSetEqual(
            {'one'},
            {
                association.attr_name
                for association
                in _EntityTypeAssociationRegistry.get_associations(self._Some)
            },
        )

        entity_some = self._Some()
        entity_one = self._One()

        entity_some.one = entity_one
        self.assertIs(entity_one, entity_some.one)

        del entity_some.one
        self.assertIsNone(entity_some.one)

    def test_pickle(self) -> None:
        entity = self._Some()
        pickle.dumps(entity)


class OneToOneTest(TestCase):
    @one_to_one('other_one', 'one')
    class _One(Entity):
        other_one: Optional[OneToOneTest._OtherOne]

    @one_to_one('one', 'other_one')
    class _OtherOne(Entity):
        one: Optional[OneToOneTest._One]

    def test(self) -> None:
        self.assertSetEqual(
            {'one'},
            {
                association.attr_name
                for association
                in _EntityTypeAssociationRegistry.get_associations(self._OtherOne)
            },
        )

        entity_one = self._One()
        entity_other_one = self._OtherOne()

        entity_other_one.one = entity_one
        self.assertIs(entity_one, entity_other_one.one)
        self.assertEqual(entity_other_one, entity_one.other_one)

        del entity_other_one.one
        self.assertIsNone(entity_other_one.one)
        self.assertIsNone(entity_one.other_one)

    def test_pickle(self) -> None:
        entity_one = self._One()
        entity_other_one = self._OtherOne()

        entity_one.other_one = entity_other_one

        unpickled_entity_one, unpickled_entity_other_one = pickle.loads(pickle.dumps((entity_one, entity_other_one)))
        self.assertEqual(entity_other_one.id, unpickled_entity_one.other_one.id)
        self.assertEqual(entity_one.id, unpickled_entity_other_one.one.id)


class ManyToOneTest(TestCase):
    @many_to_one('one', 'many')
    class _Many(Entity):
        one: Optional[ManyToOneTest._One]

    @one_to_many('many', 'one')
    class _One(Entity):
        many: EntityCollection[ManyToOneTest._Many]

    def test(self) -> None:
        self.assertSetEqual(
            {'one'},
            {
                association.attr_name
                for association
                in _EntityTypeAssociationRegistry.get_associations(self._Many)
            },
        )

        entity_many = self._Many()
        entity_one = self._One()

        entity_many.one = entity_one
        self.assertIs(entity_one, entity_many.one)
        self.assertSequenceEqual([entity_many], entity_one.many)

        del entity_many.one
        self.assertIsNone(entity_many.one)
        self.assertSequenceEqual([], entity_one.many)

    def test_pickle(self) -> None:
        entity_many = self._Many()
        entity_one = self._One()

        entity_many.one = entity_one
        unpickled_entity_many, unpickled_entity_one = pickle.loads(pickle.dumps((entity_many, entity_one)))
        self.assertEqual(unpickled_entity_many.id, unpickled_entity_one.many[0].id)
        self.assertEqual(unpickled_entity_one.id, unpickled_entity_many.one.id)


class ToManyTest(TestCase):
    @to_many('many')
    class _One(Entity):
        many: EntityCollection[OneToManyTest._Many]

    class _Many(Entity):
        pass

    def test(self) -> None:
        self.assertSetEqual(
            {'many'},
            {
                association.attr_name
                for association
                in _EntityTypeAssociationRegistry.get_associations(self._One)
            },
        )

        entity_one = self._One()
        entity_many = self._Many()

        entity_one.many.append(entity_many)
        self.assertSequenceEqual([entity_many], entity_one.many)

        entity_one.many.remove(entity_many)
        self.assertSequenceEqual([], entity_one.many)

    def test_pickle(self) -> None:
        entity_one = self._One()
        entity_other = self._Many()
        entity_one.many.append(entity_other)
        unpickled_entity_one = pickle.loads(pickle.dumps(entity_one))
        self.assertEqual(entity_other.id, unpickled_entity_one.many[0].id)


class OneToManyTest(TestCase):
    @one_to_many('many', 'one')
    class _One(Entity):
        many: SingleTypeEntityCollection[OneToManyTest._Many]

    @many_to_one('one', 'many')
    class _Many(Entity):
        one: Optional[OneToManyTest._One]

    def test(self) -> None:
        self.assertSetEqual(
            {'many'},
            {
                association.attr_name
                for association
                in _EntityTypeAssociationRegistry.get_associations(self._One)
            },
        )

        entity_one = self._One()
        entity_many = self._Many()

        entity_one.many.append(entity_many)
        self.assertSequenceEqual([entity_many], entity_one.many)
        self.assertIs(entity_one, entity_many.one)

        entity_one.many.remove(entity_many)
        self.assertSequenceEqual([], entity_one.many)
        self.assertIsNone(entity_many.one)

    def test_pickle(self) -> None:
        entity_one = self._One()
        entity_many = self._Many()

        entity_one.many.append(entity_many)

        unpickled_entity_one, unpickled_entity_many = pickle.loads(pickle.dumps((entity_one, entity_many)))
        self.assertEqual(entity_many.id, unpickled_entity_one.many[0].id)
        self.assertEqual(entity_one.id, unpickled_entity_many.one.id)


class ManyToManyTest(TestCase):
    @many_to_many('other_many', 'many')
    class _Many(Entity):
        other_many: EntityCollection[ManyToManyTest._OtherMany]

    @many_to_many('many', 'other_many')
    class _OtherMany(Entity):
        many: EntityCollection[ManyToManyTest._Many]

    def test(self) -> None:
        self.assertSetEqual(
            {'other_many'},
            {
                association.attr_name
                for association
                in _EntityTypeAssociationRegistry.get_associations(self._Many)
            },
        )

        entity_many = self._Many()
        entity_other_many = self._OtherMany()

        entity_many.other_many.append(entity_other_many)
        self.assertSequenceEqual([entity_other_many], entity_many.other_many)
        self.assertSequenceEqual([entity_many], entity_other_many.many)

        entity_many.other_many.remove(entity_other_many)
        self.assertSequenceEqual([], entity_many.other_many)
        self.assertSequenceEqual([], entity_other_many.many)

    def test_pickle(self) -> None:
        entity_many = self._Many()
        entity_other_many = self._OtherMany()

        entity_many.other_many.append(entity_other_many)

        unpickled_entity_many, unpickled_entity_other_many = pickle.loads(pickle.dumps((entity_many, entity_other_many)))
        self.assertEqual(entity_many.id, unpickled_entity_other_many.many[0].id)
        self.assertEqual(entity_other_many.id, unpickled_entity_many.other_many[0].id)


class ManyToOneToManyTest(TestCase):
    @many_to_one_to_many('one', 'left_many', 'right_many', 'one')
    class _One(Entity):
        left_many: Optional[ManyToOneToManyTest._Many]
        right_many: Optional[ManyToOneToManyTest._Many]

    @one_to_many('one', 'many')
    class _Many(Entity):
        one: EntityCollection[ManyToOneToManyTest._One]

    def test(self) -> None:
        self.assertSetEqual(
            {'left_many', 'right_many'},
            {
                association.attr_name
                for association
                in _EntityTypeAssociationRegistry.get_associations(self._One)
            },
        )

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
        entity_one = self._One()
        entity_left_many = self._Many()
        entity_right_many = self._Many()

        entity_one.left_many = entity_left_many
        entity_one.right_many = entity_right_many

        unpickled_entity_one = pickle.loads(pickle.dumps(entity_one))
        self.assertEqual(entity_left_many.id, unpickled_entity_one.left_many.id)
        self.assertEqual(entity_right_many.id, unpickled_entity_one.right_many.id)
