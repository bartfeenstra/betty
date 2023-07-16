from __future__ import annotations

from typing import Any, Iterator

import dill
import pytest

from betty.model import get_entity_type_name, Entity, get_entity_type, _EntityTypeAssociation, \
    _EntityTypeAssociationRegistry, SingleTypeEntityCollection, _AssociateCollection, MultipleTypesEntityCollection, \
    one_to_many, many_to_one_to_many, FlattenedEntityCollection, many_to_many, \
    EntityCollection, to_many, many_to_one, to_one, one_to_one, EntityTypeInvalidError, \
    EntityTypeImportError, AliasedEntity
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


class Test_EntityTypeAssociationRegistry:
    class _ParentEntity(Entity):
        pass

    class _ChildEntity(_ParentEntity):
        pass

    @pytest.fixture(scope='class', autouse=True)
    def registrations(self) -> Iterator[tuple[_EntityTypeAssociation[Any, Any], _EntityTypeAssociation[Any, Any]]]:
        parent_registration = _EntityTypeAssociation[Any, Any](self._ParentEntity, 'parent_associate', _EntityTypeAssociation.Cardinality.ONE)
        _EntityTypeAssociationRegistry.register(parent_registration)
        child_registration = _EntityTypeAssociation[Any, Any](self._ChildEntity, 'child_associate', _EntityTypeAssociation.Cardinality.MANY)
        _EntityTypeAssociationRegistry.register(child_registration)
        yield parent_registration, child_registration
        _EntityTypeAssociationRegistry._registrations.remove(parent_registration)
        _EntityTypeAssociationRegistry._registrations.remove(child_registration)

    def test_get_associations_with_parent_class_should_return_parent_associations(
        self,
        registrations: tuple[_EntityTypeAssociation[Any, Any], _EntityTypeAssociation[Any, Any]],
    ) -> None:
        parent_registration, _ = registrations
        assert {parent_registration} == _EntityTypeAssociationRegistry.get_associations(self._ParentEntity)

    def test_get_associations_with_child_class_should_return_child_associations(
        self,
        registrations: tuple[_EntityTypeAssociation[Any, Any], _EntityTypeAssociation[Any, Any]],
    ) -> None:
        parent_registration, child_registration = registrations
        assert {parent_registration, child_registration} == _EntityTypeAssociationRegistry.get_associations(self._ChildEntity)


class SingleTypeEntityCollectionTestEntity(Entity):
    pass


class TestSingleTypeEntityCollection:
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


class TestAssociateCollection:
    class _SelfReferentialEntity(Entity):
        def __init__(self, entity_id: str | None = None):
            super().__init__(entity_id)
            self.other_selfs = TestAssociateCollection._TrackingAssociateCollection(self)

    class _TrackingAssociateCollection(_AssociateCollection[Entity, Entity]):
        def __init__(self, owner: TestAssociateCollection._SelfReferentialEntity):
            super().__init__(owner, TestAssociateCollection._SelfReferentialEntity)
            self.added: list[Entity] = []
            self.removed: list[Entity] = []

        def _on_add(self, associate: Entity) -> None:
            self.added.append(associate)

        def _on_remove(self, associate: Entity) -> None:
            self.removed.append(associate)

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
    def test_prepend(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other1 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other2 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other3 = MultipleTypesEntityCollectionTestEntityOther()
        sut.prepend(entity_one, entity_other1, entity_other2, entity_other3)
        assert [entity_other3, entity_other2, entity_other1] == list(sut[MultipleTypesEntityCollectionTestEntityOther])

    def test_append(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other1 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other2 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other3 = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity_one, entity_other1, entity_other2, entity_other3)
        assert [entity_other1, entity_other2, entity_other3] == list(sut[MultipleTypesEntityCollectionTestEntityOther])

    def test_remove(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].append(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].append(entity_other)
        sut.remove(entity_one)
        assert [entity_other] == list(list(sut))
        sut.remove(entity_other)
        assert [] == list(list(sut))

    def test_getitem_by_index(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity_one, entity_other)
        assert entity_one is sut[0]
        assert entity_other is sut[1]
        with pytest.raises(IndexError):
            sut[2]

    def test_getitem_by_indices(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity_one, entity_other)
        assert [entity_one] == list(sut[0:1:1])
        assert [entity_other] == list(sut[1::1])

    def test_getitem_by_entity_type(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity_one, entity_other)
        assert [entity_one] == list(sut[MultipleTypesEntityCollectionTestEntityOne])
        assert [entity_other] == list(sut[MultipleTypesEntityCollectionTestEntityOther])
        # Ensure that getting previously unseen entity types automatically creates and returns a new collection.
        assert [] == list(sut[Entity])

    def test_getitem_by_entity_type_name(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        # Use an existing ancestry entity type, because converting an entity type name to an entity type only works for
        # entity types in a single module namespace.
        entity = Person(None)
        sut.append(entity)
        assert [entity] == list(sut['Person'])
        # Ensure that getting previously unseen entity types automatically creates and returns a new collection.
        with pytest.raises(ValueError):
            sut['NonExistentEntityType']

    def test_delitem_by_index(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity1 = MultipleTypesEntityCollectionTestEntityOne()
        entity2 = MultipleTypesEntityCollectionTestEntityOne()
        entity3 = MultipleTypesEntityCollectionTestEntityOne()
        sut.append(entity1, entity2, entity3)

        del sut[1]

        assert [entity1, entity3] == list(sut)

    def test_delitem_by_indices(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity1 = MultipleTypesEntityCollectionTestEntityOne()
        entity2 = MultipleTypesEntityCollectionTestEntityOne()
        entity3 = MultipleTypesEntityCollectionTestEntityOne()
        sut.append(entity1, entity2, entity3)

        del sut[0::2]

        assert [entity2] == list(sut)

    def test_delitem_by_entity(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity1 = MultipleTypesEntityCollectionTestEntityOne()
        entity2 = MultipleTypesEntityCollectionTestEntityOne()
        entity3 = MultipleTypesEntityCollectionTestEntityOne()
        sut.append(entity1, entity2, entity3)

        del sut[entity2]

        assert [entity1, entity3] == list(sut)

    def test_delitem_by_entity_type(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity, entity_other)

        del sut[get_entity_type(MultipleTypesEntityCollectionTestEntityOne)]

        assert [entity_other] == list(sut)

    def test_delitem_by_entity_type_name(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.append(entity, entity_other)

        del sut[get_entity_type_name(MultipleTypesEntityCollectionTestEntityOne)]

        assert [entity_other] == list(sut)

    def test_iter(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].append(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].append(entity_other)
        assert [entity_one, entity_other] == list(list(sut))

    def test_len(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].append(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].append(entity_other)
        assert 2 == len(sut)

    def test_contain_by_entity(self) -> None:
        sut = MultipleTypesEntityCollection[Any]()
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
    def test_contains_by_unsupported_type(self, value: Any) -> None:
        sut = MultipleTypesEntityCollection[Any]()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        sut.append(entity)

        assert value not in sut


class TestFlattenedEntityCollection:
    @to_one['_ToOne_Right', '_ToOne_Left']('to_one')
    class _ToOne_Left(Entity):
        to_one: TestFlattenedEntityCollection._ToOne_Right | None

    class _ToOne_Right(Entity):
        pass

    @one_to_one['_OneToOne', '_OneToOne']('to_one', 'to_one')
    class _OneToOne(Entity):
        to_one: TestFlattenedEntityCollection._OneToOne | None

    @many_to_one[
        'TestFlattenedEntityCollection._ManyToOne_Right',
        'TestFlattenedEntityCollection._ManyToOne_Left',
    ]('to_one', 'to_many')
    class _ManyToOne_Left(Entity):
        to_one: TestFlattenedEntityCollection._ManyToOne_Right | None

    @one_to_many[
        'TestFlattenedEntityCollection._ManyToOne_Left',
        'TestFlattenedEntityCollection._ManyToOne_Right',
    ]('to_many', 'to_one')
    class _ManyToOne_Right(Entity):
        to_many: EntityCollection[TestFlattenedEntityCollection._ManyToOne_Left]

    @to_many['_ToMany_Right', '_ToMany_Left']('to_many')
    class _ToMany_Left(Entity):
        to_many: EntityCollection[TestFlattenedEntityCollection._ToMany_Right]

    class _ToMany_Right(Entity):
        pass

    @one_to_many[
        'TestFlattenedEntityCollection._OneToMany_Right',
        'TestFlattenedEntityCollection._OneToMany_Left',
    ]('to_many', 'to_one')
    class _OneToMany_Left(Entity):
        to_many: EntityCollection[TestFlattenedEntityCollection._OneToMany_Right]

    @many_to_one[
        'TestFlattenedEntityCollection._OneToMany_Left',
        'TestFlattenedEntityCollection._OneToMany_Right',
    ]('to_one', 'to_many')
    class _OneToMany_Right(Entity):
        to_one: TestFlattenedEntityCollection._OneToMany_Left | None

    @many_to_many[
        'TestFlattenedEntityCollection._ManyToMany_Right',
        'TestFlattenedEntityCollection._ManyToMany_Left',
    ]('to_many', 'to_many')
    class _ManyToMany_Left(Entity):
        to_many: EntityCollection[TestFlattenedEntityCollection._ManyToMany_Right]

    @many_to_many[
        'TestFlattenedEntityCollection._ManyToMany_Left',
        'TestFlattenedEntityCollection._ManyToMany_Right',
    ]('to_many', 'to_many')
    class _ManyToMany_Right(Entity):
        to_many: EntityCollection[TestFlattenedEntityCollection._ManyToMany_Left]

    @one_to_many[
        'TestFlattenedEntityCollection._ManyToOneToMany_Middle',
        'TestFlattenedEntityCollection._ManyToOneToMany_Left',
    ]('to_many', 'to_one_left')
    class _ManyToOneToMany_Left(Entity):
        to_many: EntityCollection[TestFlattenedEntityCollection._ManyToOneToMany_Middle]

    @many_to_one_to_many[
        'TestFlattenedEntityCollection._ManyToOneToMany_Left',
        'TestFlattenedEntityCollection._ManyToOneToMany_Middle',
        'TestFlattenedEntityCollection._ManyToOneToMany_Right',
    ]('to_many', 'to_one_left', 'to_one_right', 'to_many')
    class _ManyToOneToMany_Middle(Entity):
        to_one_left: TestFlattenedEntityCollection._ManyToOneToMany_Left | None
        to_one_right: TestFlattenedEntityCollection._ManyToOneToMany_Right | None

    @one_to_many[
        'TestFlattenedEntityCollection._ManyToOneToMany_Middle',
        'TestFlattenedEntityCollection._ManyToOneToMany_Right',
    ]('to_many', 'to_one_right')
    class _ManyToOneToMany_Right(Entity):
        to_many: EntityCollection[TestFlattenedEntityCollection._ManyToOneToMany_Middle]

    def test_to_one_aliased(self) -> None:
        left = AliasedEntity(self._ToOne_Left())
        right = AliasedEntity(self._ToOne_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._ToOne_Left, left.id, 'to_one', self._ToOne_Right, right.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._ToOne_Left][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._ToOne_Right][right.unalias().id]
        assert left.unalias().to_one is right.unalias()

    def test_to_one_unaliased(self) -> None:
        left = self._ToOne_Left()
        right = self._ToOne_Right()
        left.to_one = right

        sut = FlattenedEntityCollection()
        sut.add_entity(left, right)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left is not unaliased_entities[self._ToOne_Left][left.id]
        assert right is not unaliased_entities[self._ToOne_Right][right.id]
        assert left.to_one is right

    def test_one_to_one_aliased_with_left_association(self) -> None:
        left = AliasedEntity(self._OneToOne())
        right = AliasedEntity(self._OneToOne())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._OneToOne, left.id, 'to_one', self._OneToOne, right.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._OneToOne][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._OneToOne][right.unalias().id]
        assert left.unalias().to_one is right.unalias()
        assert right.unalias().to_one is left.unalias()

    def test_one_to_one_aliased_with_right_association(self) -> None:
        left = AliasedEntity(self._OneToOne())
        right = AliasedEntity(self._OneToOne())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._OneToOne, right.id, 'to_one', self._OneToOne, left.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._OneToOne][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._OneToOne][right.unalias().id]
        assert left.unalias().to_one is right.unalias()
        assert right.unalias().to_one is left.unalias()

    def test_one_to_one_unaliased(self) -> None:
        left = self._OneToOne()
        right = self._OneToOne()
        left.to_one = right

        sut = FlattenedEntityCollection()
        sut.add_entity(left, right)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left is not unaliased_entities[self._OneToOne][left.id]
        assert right is not unaliased_entities[self._OneToOne][right.id]
        assert left.to_one is right
        assert right.to_one is left

    def test_many_to_one_aliased_with_left_association(self) -> None:
        left = AliasedEntity(self._ManyToOne_Left())
        right = AliasedEntity(self._ManyToOne_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._ManyToOne_Left, left.id, 'to_one', self._ManyToOne_Right, right.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._ManyToOne_Left][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._ManyToOne_Right][right.unalias().id]
        assert right.unalias() is left.unalias().to_one
        assert left.unalias() in right.unalias().to_many

    def test_many_to_one_aliased_with_right_association(self) -> None:
        left = AliasedEntity(self._ManyToOne_Left())
        right = AliasedEntity(self._ManyToOne_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._ManyToOne_Right, right.id, 'to_many', self._ManyToOne_Left, left.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._ManyToOne_Left][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._ManyToOne_Right][right.unalias().id]
        assert right.unalias() is left.unalias().to_one
        assert left.unalias() in right.unalias().to_many

    def test_many_to_one_unaliased(self) -> None:
        left = self._ManyToOne_Left()
        right = self._ManyToOne_Right()
        left.to_one = right

        sut = FlattenedEntityCollection()
        sut.add_entity(left, right)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left is not unaliased_entities[self._ManyToOne_Left][left.id]
        assert right is not unaliased_entities[self._ManyToOne_Right][right.id]
        assert right is left.to_one
        assert left in right.to_many

    def test_to_many_aliased(self) -> None:
        left = AliasedEntity(self._ToMany_Left())
        right = AliasedEntity(self._ToMany_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._ToMany_Left, left.id, 'to_many', self._ToMany_Right, right.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._ToMany_Left][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._ToMany_Right][right.unalias().id]
        assert right.unalias() in left.unalias().to_many

    def test_to_many_unaliased(self) -> None:
        left = self._ToMany_Left()
        right = self._ToMany_Right()
        left.to_many.append(right)

        sut = FlattenedEntityCollection()
        sut.add_entity(left, right)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left is not unaliased_entities[self._ToMany_Left][left.id]
        assert right is not unaliased_entities[self._ToMany_Right][right.id]
        assert right in left.to_many

    def test_one_to_many_aliased_with_left_association(self) -> None:
        left = AliasedEntity(self._OneToMany_Left())
        right = AliasedEntity(self._OneToMany_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._OneToMany_Left, left.id, 'to_many', self._OneToMany_Right, right.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._OneToMany_Left][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._OneToMany_Right][right.unalias().id]
        assert right.unalias() in left.unalias().to_many
        assert left.unalias() is right.unalias().to_one

    def test_one_to_many_aliased_with_right_association(self) -> None:
        left = AliasedEntity(self._OneToMany_Left())
        right = AliasedEntity(self._OneToMany_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._OneToMany_Right, right.id, 'to_one', self._OneToMany_Left, left.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._OneToMany_Left][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._OneToMany_Right][right.unalias().id]
        assert right.unalias() in left.unalias().to_many
        assert left.unalias() is right.unalias().to_one

    def test_one_to_many_unaliased(self) -> None:
        left = self._OneToMany_Left()
        right = self._OneToMany_Right()
        left.to_many.append(right)

        sut = FlattenedEntityCollection()
        sut.add_entity(left, right)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left is not unaliased_entities[self._OneToMany_Left][left.id]
        assert right is not unaliased_entities[self._OneToMany_Right][right.id]
        assert right in left.to_many
        assert left is right.to_one

    def test_many_to_many_aliased_with_left_association(self) -> None:
        left = AliasedEntity(self._ManyToMany_Left())
        right = AliasedEntity(self._ManyToMany_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._ManyToMany_Left, left.id, 'to_many', self._ManyToMany_Right, right.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._ManyToMany_Left][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._ManyToMany_Right][right.unalias().id]
        assert right.unalias() in left.unalias().to_many
        assert left.unalias() in right.unalias().to_many

    def test_many_to_many_aliased_with_right_association(self) -> None:
        left = AliasedEntity(self._ManyToMany_Left())
        right = AliasedEntity(self._ManyToMany_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._ManyToMany_Right, right.id, 'to_many', self._ManyToMany_Left, left.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._ManyToMany_Left][left.unalias().id]
        assert right.unalias() is unaliased_entities[self._ManyToMany_Right][right.unalias().id]
        assert right.unalias() in left.unalias().to_many
        assert left.unalias() in right.unalias().to_many

    def test_many_to_many_unaliased(self) -> None:
        left = self._ManyToMany_Left()
        right = self._ManyToMany_Right()
        left.to_many.append(right)

        sut = FlattenedEntityCollection()
        sut.add_entity(left, right)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left is not unaliased_entities[self._ManyToMany_Left][left.id]
        assert right is not unaliased_entities[self._ManyToMany_Right][right.id]
        assert right in left.to_many
        assert left in right.to_many

    def test_many_to_one_to_many_aliased(self) -> None:
        left = AliasedEntity(self._ManyToOneToMany_Left())
        middle = AliasedEntity(self._ManyToOneToMany_Middle())
        right = AliasedEntity(self._ManyToOneToMany_Right())

        sut = FlattenedEntityCollection()
        sut.add_entity(
            left,  # type: ignore[arg-type]
            middle,  # type: ignore[arg-type]
            right,  # type: ignore[arg-type]
        )
        sut.add_association(self._ManyToOneToMany_Middle, middle.id, 'to_one_left', self._ManyToOneToMany_Left, left.id)
        sut.add_association(self._ManyToOneToMany_Middle, middle.id, 'to_one_right', self._ManyToOneToMany_Right, right.id)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left.unalias() is unaliased_entities[self._ManyToOneToMany_Left][left.unalias().id]
        assert middle.unalias() is unaliased_entities[self._ManyToOneToMany_Middle][middle.unalias().id]
        assert right.unalias() is unaliased_entities[self._ManyToOneToMany_Right][right.unalias().id]
        assert middle.unalias() in left.unalias().to_many
        assert left.unalias() is middle.unalias().to_one_left
        assert right.unalias() is middle.unalias().to_one_right
        assert middle.unalias() in right.unalias().to_many

    def test_many_to_one_to_many_unaliased(self) -> None:
        left = self._ManyToOneToMany_Left()
        middle = self._ManyToOneToMany_Middle()
        right = self._ManyToOneToMany_Right()
        middle.to_one_left = left
        middle.to_one_right = right

        sut = FlattenedEntityCollection()
        sut.add_entity(left, middle, right)

        # Assert the result is pickleable.
        dill.loads(dill.dumps(sut)).unflatten()

        unaliased_entities = sut.unflatten()

        assert left is not unaliased_entities[self._ManyToOneToMany_Left][left.id]
        assert middle is not unaliased_entities[self._ManyToOneToMany_Middle][middle.id]
        assert right is not unaliased_entities[self._ManyToOneToMany_Right][right.id]
        assert middle in left.to_many
        assert left is middle.to_one_left
        assert right is middle.to_one_right
        assert middle in right.to_many


class TestToOne:
    @to_one['TestToOne._One', 'TestToOne._Some']('one')
    class _Some(Entity):
        one: TestToOne._One | None

    class _One(Entity):
        pass

    def test(self) -> None:
        assert {'one'} == {
            association.owner_attr_name
            for association
            in _EntityTypeAssociationRegistry.get_associations(self._Some)
        }

        entity_some = self._Some()
        entity_one = self._One()

        entity_some.one = entity_one
        assert entity_one is entity_some.one

        del entity_some.one
        assert entity_some.one is None


class TestOneToOne:
    @one_to_one['TestOneToOne._OtherOne', 'TestOneToOne._One']('other_one', 'one')
    class _One(Entity):
        other_one: TestOneToOne._OtherOne | None

    @one_to_one['TestOneToOne._One', 'TestOneToOne._OtherOne']('one', 'other_one')
    class _OtherOne(Entity):
        one: TestOneToOne._One | None

    def test(self) -> None:
        assert {'one'} == {
            association.owner_attr_name
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

        unpickled_entity_one, unpickled_entity_other_one = dill.loads(dill.dumps((entity_one, entity_other_one)))
        assert entity_other_one.id == unpickled_entity_one.other_one.id
        assert entity_one.id == unpickled_entity_other_one.one.id


class TestManyToOne:
    @many_to_one['TestManyToOne._One', 'TestManyToOne._Many']('one', 'many')
    class _Many(Entity):
        one: TestManyToOne._One | None

    @one_to_many['TestManyToOne._Many', 'TestManyToOne._One']('many', 'one')
    class _One(Entity):
        many: EntityCollection[TestManyToOne._Many]

    def test(self) -> None:
        assert {'one'} == {
            association.owner_attr_name
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
        unpickled_entity_many, unpickled_entity_one = dill.loads(dill.dumps((entity_many, entity_one)))
        assert unpickled_entity_many.id == unpickled_entity_one.many[0].id
        assert unpickled_entity_one.id == unpickled_entity_many.one.id


class TestToMany:
    @to_many['TestToMany._Many', 'TestToMany._One']('many')
    class _One(Entity):
        many: EntityCollection[TestToMany._Many]

    class _Many(Entity):
        pass

    def test(self) -> None:
        assert {'many'} == {
            association.owner_attr_name
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
        unpickled_entity_one = dill.loads(dill.dumps(entity_one))
        assert entity_other.id == unpickled_entity_one.many[0].id


class TestOneToMany:
    @one_to_many['TestOneToMany._Many', 'TestOneToMany._One']('many', 'one')
    class _One(Entity):
        many: SingleTypeEntityCollection[TestOneToMany._Many]

    @many_to_one['TestOneToMany._One', 'TestOneToMany._Many']('one', 'many')
    class _Many(Entity):
        one: TestOneToMany._One | None

    def test(self) -> None:
        assert {'many'} == {
            association.owner_attr_name
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

        unpickled_entity_one, unpickled_entity_many = dill.loads(dill.dumps((entity_one, entity_many)))
        assert entity_many.id == unpickled_entity_one.many[0].id
        assert entity_one.id == unpickled_entity_many.one.id


class TestManyToMany:
    @many_to_many['TestManyToMany._OtherMany', 'TestManyToMany._Many']('other_many', 'many')
    class _Many(Entity):
        other_many: EntityCollection[TestManyToMany._OtherMany]

    @many_to_many['TestManyToMany._Many', 'TestManyToMany._OtherMany']('many', 'other_many')
    class _OtherMany(Entity):
        many: EntityCollection[TestManyToMany._Many]

    def test(self) -> None:
        assert {'other_many'} == {
            association.owner_attr_name
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

        unpickled_entity_many, unpickled_entity_other_many = dill.loads(dill.dumps((entity_many, entity_other_many)))
        assert entity_many.id == unpickled_entity_other_many.many[0].id
        assert entity_other_many.id == unpickled_entity_many.other_many[0].id


class TestManyToOneToMany:
    @many_to_one_to_many['TestManyToOneToMany._Many', 'TestManyToOneToMany._One', 'TestManyToOneToMany._Many']('one', 'left_many', 'right_many', 'one')
    class _One(Entity):
        left_many: TestManyToOneToMany._Many | None
        right_many: TestManyToOneToMany._Many | None

    @one_to_many['TestManyToOneToMany._One', 'TestManyToOneToMany._Many']('one', 'many')
    class _Many(Entity):
        one: EntityCollection[TestManyToOneToMany._One]

    def test(self) -> None:
        assert {'left_many', 'right_many'} == {
            association.owner_attr_name
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

        unpickled_entity_one = dill.loads(dill.dumps(entity_one))
        assert entity_left_many.id == unpickled_entity_one.left_many.id
        assert entity_right_many.id == unpickled_entity_one.right_many.id
