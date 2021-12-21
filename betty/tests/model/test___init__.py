from __future__ import annotations

import copy
from typing import Optional, Any, Iterator, Tuple, List

import dill as pickle
import pytest

from betty.model import get_entity_type_name, Entity, get_entity_type, _EntityTypeAssociation, \
    _EntityTypeAssociationRegistry, SingleTypeEntityCollection, _AssociateCollection, MultipleTypesEntityCollection, \
    one_to_many, many_to_one_to_many, FlattenedEntityCollection, many_to_many, \
    EntityCollection, to_many, many_to_one, to_one, one_to_one, EntityVariation, EntityTypeInvalidError, \
    EntityTypeImportError
from betty.model.ancestry import Person


class EntityTestEntity(Entity):
    pass


class TestEntity:
    def test_id(self) -> None:
        entity_id = '000000001'
        sut = EntityTestEntity(entity_id)
        assert entity_id == sut.id


class GetEntityTypeNameTestEntity(Entity):
    pass


class TestGetEntityTypeName:
    def test_with_betty_entity(self) -> None:
        assert 'Person' == get_entity_type_name(Person)

    def test_with_other_entity(self) -> None:
        assert 'betty.tests.model.test___init__.GetEntityTypeNameTestEntity' == get_entity_type_name(GetEntityTypeNameTestEntity)


class GetEntityTypeTestEntity(Entity):
    pass


class GetEntityTypeTestEntityVariation(EntityVariation):
    pass


class GetEntityTypeTestEntityVariationEntity(GetEntityTypeTestEntityVariation, Entity):
    pass


class GetEntityTypeTestInvalidEntityAndEntityVariationSubclass(EntityVariation, Entity):
    pass


class TestGetEntityType:
    def test_with_betty_entity(self) -> None:
        assert Person == get_entity_type('Person')

    def test_with_other_entity(self) -> None:
        assert GetEntityTypeTestEntity == get_entity_type('betty.tests.model.test___init__.GetEntityTypeTestEntity')

    def test_with_unknown_entity(self) -> None:
        with pytest.raises(EntityTypeImportError):
            get_entity_type('betty_non_existent.UnknownEntity')

    def test_without_subclass(self) -> None:
        with pytest.raises(EntityTypeInvalidError):
            get_entity_type(Entity)

    def test_with_entity_subclass(self) -> None:
        assert GetEntityTypeTestEntity == get_entity_type(GetEntityTypeTestEntity)

    def test_with_entity_variation_subclass(self) -> None:
        with pytest.raises(EntityTypeInvalidError):
            get_entity_type(GetEntityTypeTestEntityVariation)

    def test_with_entity_variation_entity_subclass(self) -> None:
        assert GetEntityTypeTestEntityVariationEntity == get_entity_type(GetEntityTypeTestEntityVariationEntity)

    def test_with_invalid_entity_and_entity_variation_inheritance(self) -> None:
        with pytest.raises(EntityTypeInvalidError):
            get_entity_type(GetEntityTypeTestInvalidEntityAndEntityVariationSubclass)


class Test_EntityTypeAssociationRegistry:
    class _ParentEntity(Entity):
        pass

    class _ChildEntity(_ParentEntity):
        pass

    @pytest.fixture(scope='class', autouse=True)
    def registrations(self) -> Iterator[Tuple[_EntityTypeAssociation, _EntityTypeAssociation]]:
        parent_registration = _EntityTypeAssociation(self._ParentEntity, 'parent_associate', _EntityTypeAssociation.Cardinality.ONE)
        _EntityTypeAssociationRegistry.register(parent_registration)
        child_registration = _EntityTypeAssociation(self._ChildEntity, 'child_associate', _EntityTypeAssociation.Cardinality.MANY)
        _EntityTypeAssociationRegistry.register(child_registration)
        yield parent_registration, child_registration
        _EntityTypeAssociationRegistry._registrations.remove(parent_registration)
        _EntityTypeAssociationRegistry._registrations.remove(child_registration)

    def test_get_associations_with_parent_class_should_return_parent_associations(self, registrations) -> None:
        parent_registration, _ = registrations
        assert {parent_registration} == _EntityTypeAssociationRegistry.get_associations(self._ParentEntity)

    def test_get_associations_with_child_class_should_return_child_associations(self, registrations) -> None:
        parent_registration, child_registration = registrations
        assert {parent_registration, child_registration} == _EntityTypeAssociationRegistry.get_associations(self._ChildEntity)


class SingleTypeEntityCollectionTestEntity(Entity):
    pass


class TestSingleTypeEntityCollection:
    def test_pickle(self) -> None:
        entity = SingleTypeEntityCollectionTestEntity()
        sut = SingleTypeEntityCollection(Entity)
        sut.append(entity)
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        assert 1 == len(unpickled_sut)
        assert entity.id == unpickled_sut[0].id

    def test_copy(self) -> None:
        entity = SingleTypeEntityCollectionTestEntity()
        sut = SingleTypeEntityCollection(Entity)
        sut.append(entity)
        copied_sut = copy.copy(sut)
        assert 1 == len(copied_sut)
        assert entity.id == copied_sut[0].id

    def test_deepcopy(self) -> None:
        entity = SingleTypeEntityCollectionTestEntity()
        sut = SingleTypeEntityCollection(Entity)
        sut.append(entity)
        copied_sut = copy.deepcopy(sut)
        assert 1 == len(copied_sut)
        assert entity.id == copied_sut[0].id

    def test_prepend(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity('1')
        entity2 = SingleTypeEntityCollectionTestEntity('2')
        entity3 = SingleTypeEntityCollectionTestEntity('3')
        sut.prepend(entity3)
        sut.prepend(entity2)
        sut.prepend(entity1)
        # Prepend an already prepended value again, and assert that it was ignored.
        sut.prepend(entity1)
        assert entity1 is sut['1']
        assert entity2 is sut['2']
        assert entity3 is sut['3']

    def test_append(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity3)
        sut.append(entity2)
        sut.append(entity1)
        # Append an already appended value again, and assert that it was ignored.
        sut.append(entity1)
        assert [entity3, entity2, entity1] == list(sut)

    def test_remove(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        entity4 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3, entity4)
        sut.remove(entity4, entity2)
        assert [entity1, entity3] == list(sut)

    def test_replace(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        entity4 = SingleTypeEntityCollectionTestEntity()
        entity5 = SingleTypeEntityCollectionTestEntity()
        entity6 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)
        sut.replace(entity4, entity5, entity6)
        assert [entity4, entity5, entity6] == list(sut)

    def test_clear(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)
        sut.clear()
        assert [] == list(sut)

    def test_list(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)
        assert entity1 is sut[0]
        assert entity2 is sut[1]
        assert entity3 is sut[2]

    def test_len(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)
        assert 3 == len(sut)

    def test_iter(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)
        assert [entity1, entity2, entity3] == list(list(sut))

    def test_getitem_by_index(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)
        assert entity1 is sut[0]
        assert entity2 is sut[1]
        assert entity3 is sut[2]
        with pytest.raises(IndexError):
            sut[3]

    def test_getitem_by_indices(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)
        assert [entity1, entity3] == list(sut[0::2])

    def test_getitem_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity('1')
        entity2 = SingleTypeEntityCollectionTestEntity('2')
        entity3 = SingleTypeEntityCollectionTestEntity('3')
        sut.append(entity1, entity2, entity3)
        assert entity1 is sut['1']
        assert entity2 is sut['2']
        assert entity3 is sut['3']
        with pytest.raises(KeyError):
            sut['4']

    def test_delitem_by_index(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)

        del sut[1]

        assert [entity1, entity3] == list(sut)

    def test_delitem_by_indices(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)

        del sut[0::2]

        assert [entity2] == list(sut)

    def test_delitem_by_entity(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1, entity2, entity3)

        del sut[entity2]

        assert [entity1, entity3] == list(sut)

    def test_delitem_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity('1')
        entity2 = SingleTypeEntityCollectionTestEntity('2')
        entity3 = SingleTypeEntityCollectionTestEntity('3')
        sut.append(entity1, entity2, entity3)

        del sut['2']

        assert [entity1, entity3] == list(sut)

    def test_contains_by_entity(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1)

        assert entity1 in sut
        assert entity2 not in sut

    def test_contains_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        sut.append(entity1)

        assert entity1.id in sut
        assert entity2.id not in sut

    @pytest.mark.parametrize('value', [
        True,
        False,
        [],
    ])
    def test_contains_by_unsupported_typed(self, value: Any) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity = SingleTypeEntityCollectionTestEntity()
        sut.append(entity)

        assert value not in sut

    def test_set_like_functionality(self) -> None:
        sut = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        entity4 = SingleTypeEntityCollectionTestEntity()
        entity5 = SingleTypeEntityCollectionTestEntity()
        entity6 = SingleTypeEntityCollectionTestEntity()
        entity7 = SingleTypeEntityCollectionTestEntity()
        entity8 = SingleTypeEntityCollectionTestEntity()
        entity9 = SingleTypeEntityCollectionTestEntity()
        # Ensure duplicates are skipped.
        sut.append(entity1, entity2, entity3, entity1, entity2, entity3, entity1, entity2, entity3)
        # Ensure skipped duplicates do not affect further new values.
        sut.append(entity1, entity2, entity3, entity4, entity5, entity6, entity7, entity8, entity9)
        assert [entity1, entity2, entity3, entity4, entity5, entity6, entity7, entity8, entity9] == list(sut)

    def test_add(self) -> None:
        sut1 = SingleTypeEntityCollection(Entity)
        sut2 = SingleTypeEntityCollection(Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        sut1.append(entity1)
        sut2.append(entity2)
        sut_added = sut1 + sut2
        assert isinstance(sut_added, SingleTypeEntityCollection)
        assert [entity1, entity2] == list(sut_added)


class TestAssociateCollection:
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
            self.other_selfs = TestAssociateCollection._TrackingAssociateCollection(self)

    class _TrackingAssociateCollection(_AssociateCollection[Entity, Entity]):
        def __init__(self, owner: TestAssociateCollection._SelfReferentialEntity):
            super().__init__(owner, TestAssociateCollection._SelfReferentialEntity)
            self.added: List[Entity] = []
            self.removed: List[Entity] = []

        def _on_add(self, associate: Entity) -> None:
            self.added.append(associate)

        def _on_remove(self, associate: Entity) -> None:
            self.removed.append(associate)

    class _NoOpAssociateCollection(_AssociateCollection[Entity, Entity]):
        def __init__(self, owner: TestAssociateCollection._SelfReferentialEntity):
            super().__init__(owner, TestAssociateCollection._SelfReferentialEntity)

        def _on_add(self, associate: Entity) -> None:
            pass

        def _on_remove(self, associate: Entity) -> None:
            pass

    def test_pickle(self) -> None:
        owner = self._SelfReferentialEntity()
        associate = self._SelfReferentialEntity()
        sut = self._NoOpAssociateCollection(owner)
        sut.append(associate)
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        assert 1 == len(unpickled_sut)
        assert associate.id == unpickled_sut[0].id

    def test_copy(self) -> None:
        owner = self._SelfReferentialEntity()
        associate = self._SelfReferentialEntity()
        sut = self._NoOpAssociateCollection(owner)
        sut.append(associate)
        copied_sut = copy.copy(sut)
        assert 1 == len(copied_sut)
        assert associate.id == copied_sut[0].id

    def test_deepcopy(self) -> None:
        owner = self._SelfReferentialEntity()
        associate = self._SelfReferentialEntity()
        sut = self._NoOpAssociateCollection(owner)
        sut.append(associate)
        copied_sut = copy.deepcopy(sut)
        assert 1 == len(copied_sut)
        assert associate.id == copied_sut[0].id

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
        assert associate1 is sut['1']
        assert associate2 is sut['2']
        assert associate3 is sut['3']
        assert associate3 is sut.added[0]
        assert associate2 is sut.added[1]
        assert associate1 is sut.added[2]
        assert [] == list(sut.removed)

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
        assert [associate3, associate2, associate1] == list(sut)
        assert [associate3, associate2, associate1] == list(sut.added)
        assert [] == list(sut.removed)

    def test_remove(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        associate4 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3, associate4)
        sut.remove(associate4, associate2)
        assert [associate1, associate3] == list(sut)
        assert [associate1, associate2, associate3, associate4] == list(sut.added)
        assert [associate4, associate2] == list(sut.removed)

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
        assert [associate4, associate5, associate6] == list(sut)
        assert [associate1, associate2, associate3, associate4, associate5, associate6] == list(sut.added)
        assert [associate1, associate2, associate3] == list(sut.removed)

    def test_clear(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)
        sut.clear()
        assert [] == list(sut)
        assert associate1 is sut.added[0]
        assert associate2 is sut.added[1]
        assert associate3 is sut.added[2]
        assert associate1 is sut.removed[0]
        assert associate2 is sut.removed[1]
        assert associate3 is sut.removed[2]

    def test_list(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)
        assert associate1 is sut[0]
        assert associate2 is sut[1]
        assert associate3 is sut[2]

    def test_delitem_by_index(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)

        del sut[1]

        assert [associate1, associate3] == list(sut)
        assert [associate2] == list(sut.removed)

    def test_delitem_by_indices(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)

        del sut[0::2]

        assert [associate2] == list(sut)
        assert [associate1, associate3] == list(sut.removed)

    def test_delitem_by_entity(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity()
        associate2 = self._SelfReferentialEntity()
        associate3 = self._SelfReferentialEntity()
        sut.append(associate1, associate2, associate3)

        del sut[associate2]

        assert [associate1, associate3] == list(sut)
        assert [associate2] == list(sut.removed)

    def test_delitem_by_entity_id(self) -> None:
        owner = self._SelfReferentialEntity()
        sut = self._TrackingAssociateCollection(owner)
        associate1 = self._SelfReferentialEntity('1')
        associate2 = self._SelfReferentialEntity('2')
        associate3 = self._SelfReferentialEntity('3')
        sut.append(associate1, associate2, associate3)

        del sut['2']

        assert [associate1, associate3] == list(sut)
        assert [associate2] == list(sut.removed)


class MultipleTypesEntityCollectionTestEntityOne(Entity):
    pass


class MultipleTypesEntityCollectionTestEntityOther(Entity):
    pass


class TestMultipleTypesEntityCollection:
    def test_pickle(self) -> None:
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut = MultipleTypesEntityCollection()
        sut.append(entity_one, entity_other)
        unpickled_sut = pickle.loads(pickle.dumps(sut))
        assert 2 == len(unpickled_sut)
        assert 1 == len(unpickled_sut[MultipleTypesEntityCollectionTestEntityOne])
        assert 1 == len(unpickled_sut[MultipleTypesEntityCollectionTestEntityOther])
        assert entity_one.id == unpickled_sut[MultipleTypesEntityCollectionTestEntityOne][0].id
        assert entity_other.id == unpickled_sut[MultipleTypesEntityCollectionTestEntityOther][0].id

    def test_copy(self) -> None:
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut = MultipleTypesEntityCollection()
        sut.append(entity_one, entity_other)
        copied_sut = copy.copy(sut)
        assert 2 == len(copied_sut)
        assert 1 == len(copied_sut[MultipleTypesEntityCollectionTestEntityOne])
        assert 1 == len(copied_sut[MultipleTypesEntityCollectionTestEntityOther])
        assert entity_one.id == copied_sut[MultipleTypesEntityCollectionTestEntityOne][0].id
        assert entity_other.id == copied_sut[MultipleTypesEntityCollectionTestEntityOther][0].id

    def test_deepcopy(self) -> None:
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut = MultipleTypesEntityCollection()
        sut.append(entity_one, entity_other)
        copied_sut = copy.deepcopy(sut)
        assert 2 == len(copied_sut)
        assert 1 == len(copied_sut[MultipleTypesEntityCollectionTestEntityOne])
        assert 1 == len(copied_sut[MultipleTypesEntityCollectionTestEntityOther])
        assert entity_one.id == copied_sut[MultipleTypesEntityCollectionTestEntityOne][0].id
        assert entity_other.id == copied_sut[MultipleTypesEntityCollectionTestEntityOther][0].id

    def test_prepend(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other1 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other2 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other3 = MultipleTypesEntityCollectionTestEntityOther()
        sut.prepend(entity_one, entity_other1, entity_other2, entity_other3)
        assert [entity_other3, entity_other2, entity_other1] == list(sut[MultipleTypesEntityCollectionTestEntityOther])

    def test_append(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other1 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other2 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other3 = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity_one, entity_other1, entity_other2, entity_other3)
        assert [entity_other1, entity_other2, entity_other3] == list(sut[MultipleTypesEntityCollectionTestEntityOther])

    def test_remove(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].append(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].append(entity_other)
        sut.remove(entity_one)
        assert [entity_other] == list(list(sut))
        sut.remove(entity_other)
        assert [] == list(list(sut))

    def test_getitem_by_index(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity_one, entity_other)
        assert entity_one is sut[0]
        assert entity_other is sut[1]
        with pytest.raises(IndexError):
            sut[2]

    def test_getitem_by_indices(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity_one, entity_other)
        assert [entity_one] == list(sut[0:1:1])
        assert [entity_other] == list(sut[1::1])

    def test_getitem_by_entity_type(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity_one, entity_other)
        assert [entity_one] == list(sut[MultipleTypesEntityCollectionTestEntityOne])
        assert [entity_other] == list(sut[MultipleTypesEntityCollectionTestEntityOther])
        # Ensure that getting previously unseen entity types automatically creates and returns a new collection.
        assert [] == list(sut[Entity])

    def test_getitem_by_entity_type_name(self) -> None:
        sut = MultipleTypesEntityCollection()
        # Use an existing ancestry entity type, because converting an entity type name to an entity type only works for
        # entity types in a single module namespace.
        entity = Person(None)
        sut.append(entity)
        assert [entity] == list(sut['Person'])
        # Ensure that getting previously unseen entity types automatically creates and returns a new collection.
        with pytest.raises(ValueError):
            sut['NonExistentEntityType']

    def test_delitem_by_index(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity1 = MultipleTypesEntityCollectionTestEntityOne()
        entity2 = MultipleTypesEntityCollectionTestEntityOne()
        entity3 = MultipleTypesEntityCollectionTestEntityOne()
        sut.append(entity1, entity2, entity3)

        del sut[1]

        assert [entity1, entity3] == list(sut)

    def test_delitem_by_indices(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity1 = MultipleTypesEntityCollectionTestEntityOne()
        entity2 = MultipleTypesEntityCollectionTestEntityOne()
        entity3 = MultipleTypesEntityCollectionTestEntityOne()
        sut.append(entity1, entity2, entity3)

        del sut[0::2]

        assert [entity2] == list(sut)

    def test_delitem_by_entity(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity1 = MultipleTypesEntityCollectionTestEntityOne()
        entity2 = MultipleTypesEntityCollectionTestEntityOne()
        entity3 = MultipleTypesEntityCollectionTestEntityOne()
        sut.append(entity1, entity2, entity3)

        del sut[entity2]

        assert [entity1, entity3] == list(sut)

    def test_delitem_by_entity_type(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity, entity_other)

        del sut[get_entity_type(MultipleTypesEntityCollectionTestEntityOne)]

        assert [entity_other] == list(sut)

    def test_delitem_by_entity_type_name(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity, entity_other)

        del sut[get_entity_type_name(MultipleTypesEntityCollectionTestEntityOne)]

        assert [entity_other] == list(sut)

    def test_iter(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].append(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].append(entity_other)
        assert [entity_one, entity_other] == list(list(sut))

    def test_len(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].append(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].append(entity_other)
        assert 2 == len(sut)

    def test_contain_by_entity(self) -> None:
        sut = MultipleTypesEntityCollection()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other1 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other2 = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].append(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].append(entity_other1)
        assert entity_one in sut
        assert entity_other1 in sut
        assert entity_other2 not in sut

    @pytest.mark.parametrize('value', [
        True,
        False,
        [],
    ])
    def test_contains_by_unsupported_typed(self, value: Any) -> None:
        sut = MultipleTypesEntityCollection()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        sut.append(entity)

        assert value not in sut

    def test_add(self) -> None:
        sut1 = MultipleTypesEntityCollection()
        sut2 = MultipleTypesEntityCollection()
        entity1_one = MultipleTypesEntityCollectionTestEntityOne()
        entity1_other = MultipleTypesEntityCollectionTestEntityOne()
        entity2_one = MultipleTypesEntityCollectionTestEntityOther()
        entity2_other = MultipleTypesEntityCollectionTestEntityOther()
        sut1.append(entity1_one, entity1_other)
        sut2.append(entity2_one, entity2_other)
        sut_added = sut1 + sut2
        assert isinstance(sut_added, MultipleTypesEntityCollection)
        assert [entity1_one, entity1_other, entity2_one, entity2_other] == list(sut_added)


class TestFlattenedEntityCollection:
    @many_to_many('other_many', 'many')
    class _ManyToMany_Many(Entity):
        other_many: EntityCollection[TestFlattenedEntityCollection._ManyToMany_OtherMany]

    @many_to_many('many', 'other_many')
    class _ManyToMany_OtherMany(Entity):
        many: EntityCollection[TestFlattenedEntityCollection._ManyToMany_Many]

    @one_to_many('other_many', 'many')
    class _ManyToOneToMany_Many(Entity):
        other_many: EntityCollection[TestFlattenedEntityCollection._ManyToOneToMany_OtherMany]

    @many_to_one_to_many('other_many', 'many', 'other_many', 'many')
    class _ManyToOneToMany_One(Entity):
        many: TestFlattenedEntityCollection._ManyToOneToMany_Many
        other_many: TestFlattenedEntityCollection._ManyToOneToMany_OtherMany

    @one_to_many('many', 'other_many')
    class _ManyToOneToMany_OtherMany(Entity):
        many: EntityCollection[TestFlattenedEntityCollection._ManyToOneToMany_Many]

    def test_add_to_many_association_then_unflatten(self) -> None:
        entity_many = self._ManyToMany_Many()
        entity_other_many = self._ManyToMany_OtherMany()

        flattened_entities = FlattenedEntityCollection()
        flattened_entities.add_entity(entity_many, entity_other_many)
        flattened_entities.add_association(self._ManyToMany_Many, entity_many.id, 'other_many', self._ManyToMany_OtherMany, entity_other_many.id)

        # Assert the result is pickleable.
        pickle.dumps(flattened_entities)

        unflattened_entities = flattened_entities.unflatten()

        unflattened_entity_many: TestFlattenedEntityCollection._ManyToMany_Many = unflattened_entities[self._ManyToMany_Many][0]
        unflattened_entity_other_many: TestFlattenedEntityCollection._ManyToMany_OtherMany = unflattened_entities[self._ManyToMany_OtherMany][0]
        assert entity_many is not unflattened_entity_many
        assert entity_other_many is not unflattened_entity_other_many
        assert 1 == len(unflattened_entity_other_many.many)
        assert unflattened_entity_many in unflattened_entity_other_many.many
        assert 1 == len(unflattened_entity_many.other_many)
        assert unflattened_entity_other_many in unflattened_entity_many.other_many

    def test_add_entity_with_to_many_association_then_unflatten(self) -> None:
        entity_many = self._ManyToMany_Many()
        entity_other_many = self._ManyToMany_OtherMany()
        entity_many.other_many.append(entity_other_many)

        flattened_entities = FlattenedEntityCollection()
        flattened_entities.add_entity(entity_many, entity_other_many)

        # Assert the original entities remain unchanged.
        assert entity_many in entity_other_many.many
        assert entity_other_many in entity_many.other_many
        # Assert the result is pickleable.
        pickle.dumps(flattened_entities)

        unflattened_entities = flattened_entities.unflatten()

        unflattened_entity_many = unflattened_entities[self._ManyToMany_Many][0]
        unflattened_entity_other_many = unflattened_entities[self._ManyToMany_OtherMany][0]
        assert entity_many is not unflattened_entity_many
        assert entity_other_many is not unflattened_entity_other_many
        assert unflattened_entity_many in unflattened_entity_other_many.many
        assert unflattened_entity_other_many in unflattened_entity_many.other_many

    def test_add_entity_with_many_to_one_to_many_association_then_unflatten(self) -> None:
        entity_many = self._ManyToOneToMany_Many()
        entity_one = self._ManyToOneToMany_One()
        entity_other_many = self._ManyToOneToMany_OtherMany()
        entity_one.many = entity_many
        entity_one.other_many = entity_other_many

        flattened_entities = FlattenedEntityCollection()
        flattened_entities.add_entity(entity_many, entity_one, entity_other_many)

        # Assert the original entities remain unchanged.
        assert entity_many is entity_one.many
        assert entity_other_many is entity_one.other_many
        # Assert the result is pickleable.
        pickle.dumps(flattened_entities)

        unflattened_entities: Tuple[
            TestFlattenedEntityCollection._ManyToOneToMany_Many,
            TestFlattenedEntityCollection._ManyToOneToMany_One,
            TestFlattenedEntityCollection._ManyToOneToMany_OtherMany,
        ] = flattened_entities.unflatten()  # type: ignore
        unflattened_entity_many, unflattened_entity_one, unflattened_entity_other_many = unflattened_entities

        assert entity_many is not unflattened_entity_many
        assert entity_other_many is not unflattened_entity_other_many
        assert unflattened_entity_one in unflattened_entity_other_many.many
        assert unflattened_entity_one in unflattened_entity_many.other_many
        assert unflattened_entity_many is unflattened_entity_one.many
        assert unflattened_entity_other_many is unflattened_entity_one.other_many


class TestToOne:
    @to_one('one')
    class _Some(Entity):
        one: Optional[TestToOne._One]

    class _One(Entity):
        pass

    def test(self) -> None:
        assert {'one'} == {
            association.attr_name
            for association
            in _EntityTypeAssociationRegistry.get_associations(self._Some)
        }

        entity_some = self._Some()
        entity_one = self._One()

        entity_some.one = entity_one
        assert entity_one is entity_some.one

        del entity_some.one
        assert entity_some.one is None

    def test_pickle(self) -> None:
        entity = self._Some()
        pickle.dumps(entity)


class TestOneToOne:
    @one_to_one('other_one', 'one')
    class _One(Entity):
        other_one: Optional[TestOneToOne._OtherOne]

    @one_to_one('one', 'other_one')
    class _OtherOne(Entity):
        one: Optional[TestOneToOne._One]

    def test(self) -> None:
        assert {'one'} == {
            association.attr_name
            for association
            in _EntityTypeAssociationRegistry.get_associations(self._OtherOne)
        }

        entity_one = self._One()
        entity_other_one = self._OtherOne()

        entity_other_one.one = entity_one
        assert entity_one is entity_other_one.one
        assert entity_other_one == entity_one.other_one

        del entity_other_one.one
        assert entity_other_one.one is None
        assert entity_one.other_one is None

    def test_pickle(self) -> None:
        entity_one = self._One()
        entity_other_one = self._OtherOne()

        entity_one.other_one = entity_other_one

        unpickled_entity_one, unpickled_entity_other_one = pickle.loads(pickle.dumps((entity_one, entity_other_one)))
        assert entity_other_one.id == unpickled_entity_one.other_one.id
        assert entity_one.id == unpickled_entity_other_one.one.id


class TestManyToOne:
    @many_to_one('one', 'many')
    class _Many(Entity):
        one: Optional[TestManyToOne._One]

    @one_to_many('many', 'one')
    class _One(Entity):
        many: EntityCollection[TestManyToOne._Many]

    def test(self) -> None:
        assert {'one'} == {
            association.attr_name
            for association
            in _EntityTypeAssociationRegistry.get_associations(self._Many)
        }

        entity_many = self._Many()
        entity_one = self._One()

        entity_many.one = entity_one
        assert entity_one is entity_many.one
        assert [entity_many] == list(entity_one.many)

        del entity_many.one
        assert entity_many.one is None
        assert [] == list(entity_one.many)

    def test_pickle(self) -> None:
        entity_many = self._Many()
        entity_one = self._One()

        entity_many.one = entity_one
        unpickled_entity_many, unpickled_entity_one = pickle.loads(pickle.dumps((entity_many, entity_one)))
        assert unpickled_entity_many.id == unpickled_entity_one.many[0].id
        assert unpickled_entity_one.id == unpickled_entity_many.one.id


class TestToMany:
    @to_many('many')
    class _One(Entity):
        many: EntityCollection[TestToMany._Many]

    class _Many(Entity):
        pass

    def test(self) -> None:
        assert {'many'} == {
            association.attr_name
            for association
            in _EntityTypeAssociationRegistry.get_associations(self._One)
        }

        entity_one = self._One()
        entity_many = self._Many()

        entity_one.many.append(entity_many)
        assert [entity_many] == list(entity_one.many)

        entity_one.many.remove(entity_many)
        assert [] == list(entity_one.many)

    def test_pickle(self) -> None:
        entity_one = self._One()
        entity_other = self._Many()
        entity_one.many.append(entity_other)
        unpickled_entity_one = pickle.loads(pickle.dumps(entity_one))
        assert entity_other.id == unpickled_entity_one.many[0].id


class TestOneToMany:
    @one_to_many('many', 'one')
    class _One(Entity):
        many: SingleTypeEntityCollection[TestOneToMany._Many]

    @many_to_one('one', 'many')
    class _Many(Entity):
        one: Optional[TestOneToMany._One]

    def test(self) -> None:
        assert {'many'} == {
            association.attr_name
            for association
            in _EntityTypeAssociationRegistry.get_associations(self._One)
        }

        entity_one = self._One()
        entity_many = self._Many()

        entity_one.many.append(entity_many)
        assert [entity_many] == list(entity_one.many)
        assert entity_one is entity_many.one

        entity_one.many.remove(entity_many)
        assert [] == list(entity_one.many)
        assert entity_many.one is None

    def test_pickle(self) -> None:
        entity_one = self._One()
        entity_many = self._Many()

        entity_one.many.append(entity_many)

        unpickled_entity_one, unpickled_entity_many = pickle.loads(pickle.dumps((entity_one, entity_many)))
        assert entity_many.id == unpickled_entity_one.many[0].id
        assert entity_one.id == unpickled_entity_many.one.id


class TestManyToMany:
    @many_to_many('other_many', 'many')
    class _Many(Entity):
        other_many: EntityCollection[TestManyToMany._OtherMany]

    @many_to_many('many', 'other_many')
    class _OtherMany(Entity):
        many: EntityCollection[TestManyToMany._Many]

    def test(self) -> None:
        assert {'other_many'} == {
            association.attr_name
            for association
            in _EntityTypeAssociationRegistry.get_associations(self._Many)
        }

        entity_many = self._Many()
        entity_other_many = self._OtherMany()

        entity_many.other_many.append(entity_other_many)
        assert [entity_other_many] == list(entity_many.other_many)
        assert [entity_many] == list(entity_other_many.many)

        entity_many.other_many.remove(entity_other_many)
        assert [] == list(entity_many.other_many)
        assert [] == list(entity_other_many.many)

    def test_pickle(self) -> None:
        entity_many = self._Many()
        entity_other_many = self._OtherMany()

        entity_many.other_many.append(entity_other_many)

        unpickled_entity_many, unpickled_entity_other_many = pickle.loads(pickle.dumps((entity_many, entity_other_many)))
        assert entity_many.id == unpickled_entity_other_many.many[0].id
        assert entity_other_many.id == unpickled_entity_many.other_many[0].id


class TestManyToOneToMany:
    @many_to_one_to_many('one', 'left_many', 'right_many', 'one')
    class _One(Entity):
        left_many: Optional[TestManyToOneToMany._Many]
        right_many: Optional[TestManyToOneToMany._Many]

    @one_to_many('one', 'many')
    class _Many(Entity):
        one: EntityCollection[TestManyToOneToMany._One]

    def test(self) -> None:
        assert {'left_many', 'right_many'} == {
            association.attr_name
            for association
            in _EntityTypeAssociationRegistry.get_associations(self._One)
        }

        entity_one = self._One()
        entity_left_many = self._Many()
        entity_right_many = self._Many()

        entity_one.left_many = entity_left_many
        assert entity_left_many is entity_one.left_many
        assert [entity_one] == list(entity_left_many.one)

        entity_one.right_many = entity_right_many
        assert entity_right_many is entity_one.right_many
        assert [entity_one] == list(entity_right_many.one)

        del entity_one.left_many
        assert entity_one.left_many is None
        assert [] == list(entity_left_many.one)
        assert entity_one.right_many is None
        assert [] == list(entity_right_many.one)

    def test_pickle(self) -> None:
        entity_one = self._One()
        entity_left_many = self._Many()
        entity_right_many = self._Many()

        entity_one.left_many = entity_left_many
        entity_one.right_many = entity_right_many

        unpickled_entity_one = pickle.loads(pickle.dumps(entity_one))
        assert entity_left_many.id == unpickled_entity_one.left_many.id
        assert entity_right_many.id == unpickled_entity_one.right_many.id
