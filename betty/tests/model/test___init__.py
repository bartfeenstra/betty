from __future__ import annotations

from typing import Any, Iterator

import dill
import pytest

from betty.model import get_entity_type_name, Entity, get_entity_type, ToAny, \
    EntityTypeAssociationRegistry, SingleTypeEntityCollection, MultipleTypesEntityCollection, \
    one_to_many, many_to_one_to_many, many_to_many, \
    EntityCollection, to_many, many_to_one, to_one, one_to_one, EntityTypeImportError, ToOne, \
    PickleableEntityGraph, EntityGraphBuilder, AliasableEntity, AliasedEntity, unalias
from betty.model.ancestry import Person


class EntityTestEntity(Entity):
    pass


class TestEntity:
    async def test_id(self) -> None:
        entity_id = '000000001'
        sut = EntityTestEntity(entity_id)
        assert entity_id == sut.id


class GetEntityTypeNameTestEntity(Entity):
    pass


class TestGetEntityTypeName:
    async def test_with_betty_entity(self) -> None:
        assert 'Person' == get_entity_type_name(Person)

    async def test_with_other_entity(self) -> None:
        assert 'betty.tests.model.test___init__.GetEntityTypeNameTestEntity' == get_entity_type_name(GetEntityTypeNameTestEntity)


class GetEntityTypeTestEntity(Entity):
    pass


class TestGetEntityType:
    async def test_with_betty_entity_type_name(self) -> None:
        assert Person == get_entity_type('Person')

    async def test_with_other_entity_type_name(self) -> None:
        assert GetEntityTypeTestEntity == get_entity_type('betty.tests.model.test___init__.GetEntityTypeTestEntity')

    async def test_with_unknown_entity_type_name(self) -> None:
        with pytest.raises(EntityTypeImportError):
            get_entity_type('betty_non_existent.UnknownEntity')


class _TestEntityTypeAssociationRegistry_ParentEntity(Entity):
    pass


class _TestEntityTypeAssociationRegistry_ChildEntity(_TestEntityTypeAssociationRegistry_ParentEntity):
    pass


class _TestEntityTypeAssociationRegistry_Associate(Entity):
    pass


class TestEntityTypeAssociationRegistry:
    @pytest.fixture(scope='class', autouse=True)
    def associations(self) -> Iterator[tuple[ToAny[Any, Any], ToAny[Any, Any]]]:
        parent_association = ToOne[
            _TestEntityTypeAssociationRegistry_ParentEntity,
            _TestEntityTypeAssociationRegistry_ChildEntity
        ](
            _TestEntityTypeAssociationRegistry_ParentEntity,
            'parent_associate',
            'betty.tests.model.test___init__._TestEntityTypeAssociationRegistry_Associate',
        )
        EntityTypeAssociationRegistry._register(parent_association)
        child_association = ToOne[
            _TestEntityTypeAssociationRegistry_ChildEntity,
            _TestEntityTypeAssociationRegistry_ParentEntity
        ](
            _TestEntityTypeAssociationRegistry_ChildEntity,
            'child_associate',
            'betty.tests.model.test___init__._TestEntityTypeAssociationRegistry_Associate',
        )
        EntityTypeAssociationRegistry._register(child_association)
        yield parent_association, child_association
        EntityTypeAssociationRegistry._associations.remove(parent_association)
        EntityTypeAssociationRegistry._associations.remove(child_association)

    async def test_get_associations_with_parent_class_should_return_parent_associations(
        self,
        associations: tuple[ToAny[Any, Any], ToAny[Any, Any]],
    ) -> None:
        parent_registration, _ = associations
        assert {parent_registration} == EntityTypeAssociationRegistry.get_all_associations(_TestEntityTypeAssociationRegistry_ParentEntity)

    async def test_get_associations_with_child_class_should_return_child_associations(
        self,
        associations: tuple[ToAny[Any, Any], ToAny[Any, Any]],
    ) -> None:
        parent_association, child_association = associations
        assert {parent_association, child_association} == EntityTypeAssociationRegistry.get_all_associations(_TestEntityTypeAssociationRegistry_ChildEntity)


class SingleTypeEntityCollectionTestEntity(Entity):
    pass


class TestSingleTypeEntityCollection:
    async def test_add(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity3)
        sut.add(entity2)
        sut.add(entity1)
        # Add an already added value again, and assert that it was ignored.
        sut.add(entity1)
        assert [entity3, entity2, entity1] == list(sut)

    async def test_add_with_duplicate_entities(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
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
        sut.add(entity1, entity2, entity3, entity1, entity2, entity3, entity1, entity2, entity3)
        assert [entity1, entity2, entity3] == list(sut)
        # Ensure skipped duplicates do not affect further new values.
        sut.add(entity1, entity2, entity3, entity4, entity5, entity6, entity7, entity8, entity9)
        assert [entity1, entity2, entity3, entity4, entity5, entity6, entity7, entity8, entity9] == list(sut)

    async def test_remove(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        entity4 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3, entity4)
        sut.remove(entity4, entity2)
        assert [entity1, entity3] == list(sut)

    async def test_replace(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        entity4 = SingleTypeEntityCollectionTestEntity()
        entity5 = SingleTypeEntityCollectionTestEntity()
        entity6 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3)
        sut.replace(entity4, entity5, entity6)
        assert [entity4, entity5, entity6] == list(sut)

    async def test_clear(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3)
        sut.clear()
        assert [] == list(sut)

    async def test_list(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3)
        assert entity1 is sut[0]
        assert entity2 is sut[1]
        assert entity3 is sut[2]

    async def test_len(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3)
        assert 3 == len(sut)

    async def test_iter(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3)
        assert [entity1, entity2, entity3] == list(list(sut))

    async def test_getitem_by_index(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3)
        assert entity1 is sut[0]
        assert entity2 is sut[1]
        assert entity3 is sut[2]
        with pytest.raises(IndexError):
            sut[3]

    async def test_getitem_by_indices(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3)
        assert [entity1, entity3] == list(sut[0::2])

    async def test_getitem_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity('1')
        entity2 = SingleTypeEntityCollectionTestEntity('2')
        entity3 = SingleTypeEntityCollectionTestEntity('3')
        sut.add(entity1, entity2, entity3)
        assert entity1 is sut['1']
        assert entity2 is sut['2']
        assert entity3 is sut['3']
        with pytest.raises(KeyError):
            sut['4']

    async def test_delitem_by_entity(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        entity3 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1, entity2, entity3)

        del sut[entity2]

        assert [entity1, entity3] == list(sut)

    async def test_delitem_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity('1')
        entity2 = SingleTypeEntityCollectionTestEntity('2')
        entity3 = SingleTypeEntityCollectionTestEntity('3')
        sut.add(entity1, entity2, entity3)

        del sut['2']

        assert [entity1, entity3] == list(sut)

    async def test_contains_by_entity(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1)

        assert entity1 in sut
        assert entity2 not in sut

    async def test_contains_by_entity_id(self) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity1 = SingleTypeEntityCollectionTestEntity()
        entity2 = SingleTypeEntityCollectionTestEntity()
        sut.add(entity1)

        assert entity1.id in sut
        assert entity2.id not in sut

    @pytest.mark.parametrize('value', [
        True,
        False,
        [],
    ])
    async def test_contains_by_unsupported_typed(self, value: Any) -> None:
        sut = SingleTypeEntityCollection[Entity](Entity)
        entity = SingleTypeEntityCollectionTestEntity()
        sut.add(entity)

        assert value not in sut


class MultipleTypesEntityCollectionTestEntityOne(Entity):
    pass


class MultipleTypesEntityCollectionTestEntityOther(Entity):
    pass


class TestMultipleTypesEntityCollection:
    async def test_add(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other1 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other2 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other3 = MultipleTypesEntityCollectionTestEntityOther()
        sut.add(entity_one, entity_other1, entity_other2, entity_other3)
        assert [entity_one] == list(sut[MultipleTypesEntityCollectionTestEntityOne])
        assert [entity_other1, entity_other2, entity_other3] == list(sut[MultipleTypesEntityCollectionTestEntityOther])

    async def test_add_with_duplicate_entities(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity1 = MultipleTypesEntityCollectionTestEntityOne()
        entity2 = MultipleTypesEntityCollectionTestEntityOther()
        entity3 = MultipleTypesEntityCollectionTestEntityOne()
        entity4 = MultipleTypesEntityCollectionTestEntityOther()
        entity5 = MultipleTypesEntityCollectionTestEntityOne()
        entity6 = MultipleTypesEntityCollectionTestEntityOther()
        entity7 = MultipleTypesEntityCollectionTestEntityOne()
        entity8 = MultipleTypesEntityCollectionTestEntityOther()
        entity9 = MultipleTypesEntityCollectionTestEntityOne()
        # Ensure duplicates are skipped.
        sut.add(entity1, entity2, entity3, entity1, entity2, entity3, entity1, entity2, entity3)
        assert [entity1, entity3] == list(sut[MultipleTypesEntityCollectionTestEntityOne])
        assert [entity2] == list(sut[MultipleTypesEntityCollectionTestEntityOther])
        # Ensure skipped duplicates do not affect further new values.
        sut.add(entity1, entity2, entity3, entity4, entity5, entity6, entity7, entity8, entity9)
        assert [entity1, entity3, entity5, entity7, entity9] == list(sut[MultipleTypesEntityCollectionTestEntityOne])
        assert [entity2, entity4, entity6, entity8] == list(sut[MultipleTypesEntityCollectionTestEntityOther])

    async def test_remove(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].add(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].add(entity_other)
        sut.remove(entity_one)
        assert [entity_other] == list(list(sut))
        sut.remove(entity_other)
        assert [] == list(list(sut))

    async def test_getitem_by_index(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.add(entity_one, entity_other)
        assert entity_one is sut[0]
        assert entity_other is sut[1]
        with pytest.raises(IndexError):
            sut[2]

    async def test_getitem_by_indices(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.add(entity_one, entity_other)
        assert [entity_one] == list(sut[0:1:1])
        assert [entity_other] == list(sut[1::1])

    async def test_getitem_by_entity_type(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.add(entity_one, entity_other)
        assert [entity_one] == list(sut[MultipleTypesEntityCollectionTestEntityOne])
        assert [entity_other] == list(sut[MultipleTypesEntityCollectionTestEntityOther])
        # Ensure that getting previously unseen entity types automatically creates and returns a new collection.
        assert [] == list(sut[Entity])

    async def test_getitem_by_entity_type_name(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        # Use an existing ancestry entity type, because converting an entity type name to an entity type only works for
        # entity types in a single module namespace.
        entity = Person(None)
        sut.add(entity)
        assert [entity] == list(sut['Person'])
        # Ensure that getting previously unseen entity types automatically creates and returns a new collection.
        with pytest.raises(ValueError):
            sut['NonExistentEntityType']

    async def test_delitem_by_entity(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity1 = MultipleTypesEntityCollectionTestEntityOne()
        entity2 = MultipleTypesEntityCollectionTestEntityOne()
        entity3 = MultipleTypesEntityCollectionTestEntityOne()
        sut.add(entity1, entity2, entity3)

        del sut[entity2]

        assert [entity1, entity3] == list(sut)

    async def test_delitem_by_entity_type(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.add(entity, entity_other)

        del sut[MultipleTypesEntityCollectionTestEntityOne]

        assert [entity_other] == list(sut)

    async def test_delitem_by_entity_type_name(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut.add(entity, entity_other)

        del sut[get_entity_type_name(MultipleTypesEntityCollectionTestEntityOne)]

        assert [entity_other] == list(sut)

    async def test_iter(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].add(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].add(entity_other)
        assert [entity_one, entity_other] == list(list(sut))

    async def test_len(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].add(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].add(entity_other)
        assert 2 == len(sut)

    async def test_contain_by_entity(self) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity_one = MultipleTypesEntityCollectionTestEntityOne()
        entity_other1 = MultipleTypesEntityCollectionTestEntityOther()
        entity_other2 = MultipleTypesEntityCollectionTestEntityOther()
        sut[MultipleTypesEntityCollectionTestEntityOne].add(entity_one)
        sut[MultipleTypesEntityCollectionTestEntityOther].add(entity_other1)
        assert entity_one in sut
        assert entity_other1 in sut
        assert entity_other2 not in sut

    @pytest.mark.parametrize('value', [
        True,
        False,
        [],
    ])
    async def test_contains_by_unsupported_type(self, value: Any) -> None:
        sut = MultipleTypesEntityCollection[Entity]()
        entity = MultipleTypesEntityCollectionTestEntityOne()
        sut.add(entity)

        assert value not in sut


@to_one(
    'to_one',
    'betty.tests.model.test___init__._EntityGraphBuilder_ToOne_Right',
)
class _EntityGraphBuilder_ToOne_Left(Entity):
    to_one: _EntityGraphBuilder_ToOne_Right | None


class _EntityGraphBuilder_ToOne_Right(Entity):
    pass


@one_to_one(
    'to_one',
    'betty.tests.model.test___init__._EntityGraphBuilder_OneToOne_Right',
    'to_one',
)
class _EntityGraphBuilder_OneToOne_Left(Entity):
    to_one: _EntityGraphBuilder_OneToOne_Right | None


@one_to_one(
    'to_one',
    'betty.tests.model.test___init__._EntityGraphBuilder_OneToOne_Left',
    'to_one',
)
class _EntityGraphBuilder_OneToOne_Right(Entity):
    to_one: _EntityGraphBuilder_OneToOne_Left | None


@many_to_one(
    'to_one',
    'betty.tests.model.test___init__._EntityGraphBuilder_ManyToOne_Right',
    'to_many',
)
class _EntityGraphBuilder_ManyToOne_Left(Entity):
    to_one: _EntityGraphBuilder_ManyToOne_Right | None


@one_to_many(
    'to_many',
    'betty.tests.model.test___init__._EntityGraphBuilder_ManyToOne_Left',
    'to_one',
)
class _EntityGraphBuilder_ManyToOne_Right(Entity):
    to_many: EntityCollection[_EntityGraphBuilder_ManyToOne_Left]


@to_many(
    'to_many',
    'betty.tests.model.test___init__._EntityGraphBuilder_ToMany_Right',
)
class _EntityGraphBuilder_ToMany_Left(Entity):
    to_many: EntityCollection[_EntityGraphBuilder_ToMany_Right]


class _EntityGraphBuilder_ToMany_Right(Entity):
    pass


@one_to_many(
    'to_many',
    'betty.tests.model.test___init__._EntityGraphBuilder_OneToMany_Right',
    'to_one',
)
class _EntityGraphBuilder_OneToMany_Left(Entity):
    to_many: EntityCollection[_EntityGraphBuilder_OneToMany_Right]


@many_to_one(
    'to_one',
    'betty.tests.model.test___init__._EntityGraphBuilder_OneToMany_Left',
    'to_many',
)
class _EntityGraphBuilder_OneToMany_Right(Entity):
    to_one: _EntityGraphBuilder_OneToMany_Left | None


@many_to_many(
    'to_many',
    'betty.tests.model.test___init__._EntityGraphBuilder_ManyToMany_Right',
    'to_many',
)
class _EntityGraphBuilder_ManyToMany_Left(Entity):
    to_many: EntityCollection[_EntityGraphBuilder_ManyToMany_Right]


@many_to_many(
    'to_many',
    'betty.tests.model.test___init__._EntityGraphBuilder_ManyToMany_Left',
    'to_many',
)
class _EntityGraphBuilder_ManyToMany_Right(Entity):
    to_many: EntityCollection[_EntityGraphBuilder_ManyToMany_Left]


@one_to_many(
    'to_many',
    'betty.tests.model.test___init__._EntityGraphBuilder_ManyToOneToMany_Middle',
    'to_one_left',
)
class _EntityGraphBuilder_ManyToOneToMany_Left(Entity):
    to_many: EntityCollection[_EntityGraphBuilder_ManyToOneToMany_Middle]


@many_to_one_to_many(
    'betty.tests.model.test___init__._EntityGraphBuilder_ManyToOneToMany_Left',
    'to_many',
    'to_one_left',
    'to_one_right',
    'betty.tests.model.test___init__._EntityGraphBuilder_ManyToOneToMany_Right',
    'to_many',
)
class _EntityGraphBuilder_ManyToOneToMany_Middle(Entity):
    to_one_left: _EntityGraphBuilder_ManyToOneToMany_Left | None
    to_one_right: _EntityGraphBuilder_ManyToOneToMany_Right | None


@one_to_many(
    'to_many',
    'betty.tests.model.test___init__._EntityGraphBuilder_ManyToOneToMany_Middle',
    'to_one_right',
)
class _EntityGraphBuilder_ManyToOneToMany_Right(Entity):
    to_many: EntityCollection[_EntityGraphBuilder_ManyToOneToMany_Middle]


class TestEntityGraphBuilder:
    @pytest.mark.parametrize('to_one_left, to_one_right', [
        (
            _EntityGraphBuilder_ToOne_Left(),
            _EntityGraphBuilder_ToOne_Right(),
        ),
        (
            AliasedEntity(_EntityGraphBuilder_ToOne_Left()),
            AliasedEntity(_EntityGraphBuilder_ToOne_Right()),
        ),
    ])
    async def test_build_to_one(
        self,
        to_one_left: AliasableEntity[_EntityGraphBuilder_ToOne_Left],
        to_one_right: AliasableEntity[_EntityGraphBuilder_ToOne_Right],
    ) -> None:
        sut = EntityGraphBuilder()
        sut.add_entity(to_one_left, to_one_right)  # type: ignore[arg-type]
        sut.add_association(
            _EntityGraphBuilder_ToOne_Left,
            to_one_left.id,
            'to_one',
            _EntityGraphBuilder_ToOne_Right,
            to_one_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_to_one_left = unalias(to_one_left)
        unaliased_to_one_right = unalias(to_one_right)

        assert unaliased_to_one_left is built_entities[_EntityGraphBuilder_ToOne_Left][unaliased_to_one_left.id]
        assert unaliased_to_one_right is built_entities[_EntityGraphBuilder_ToOne_Right][unaliased_to_one_right.id]
        assert unaliased_to_one_right is unaliased_to_one_left.to_one

    @pytest.mark.parametrize('one_to_one_left, one_to_one_right', [
        (
            _EntityGraphBuilder_OneToOne_Left(),
            _EntityGraphBuilder_OneToOne_Right(),
        ),
        (
            AliasedEntity(_EntityGraphBuilder_OneToOne_Left()),
            AliasedEntity(_EntityGraphBuilder_OneToOne_Right()),
        ),
    ])
    async def test_build_one_to_one(
        self,
        one_to_one_left: AliasableEntity[_EntityGraphBuilder_OneToOne_Left],
        one_to_one_right: AliasableEntity[_EntityGraphBuilder_OneToOne_Right],
    ) -> None:
        sut = EntityGraphBuilder()
        sut.add_entity(one_to_one_left, one_to_one_right)  # type: ignore[arg-type]
        sut.add_association(
            _EntityGraphBuilder_OneToOne_Left,
            one_to_one_left.id,
            'to_one',
            _EntityGraphBuilder_OneToOne_Right,
            one_to_one_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_one_to_one_left = unalias(one_to_one_left)
        unaliased_one_to_one_right = unalias(one_to_one_right)

        assert unaliased_one_to_one_left is built_entities[_EntityGraphBuilder_OneToOne_Left][unaliased_one_to_one_left.id]
        assert unaliased_one_to_one_right is built_entities[_EntityGraphBuilder_OneToOne_Right][unaliased_one_to_one_right.id]
        assert unaliased_one_to_one_right is unaliased_one_to_one_left.to_one
        assert unaliased_one_to_one_left is unaliased_one_to_one_right.to_one

    @pytest.mark.parametrize('many_to_one_left, many_to_one_right', [
        (
            _EntityGraphBuilder_ManyToOne_Left(),
            _EntityGraphBuilder_ManyToOne_Right(),
        ),
        (
            AliasedEntity(_EntityGraphBuilder_ManyToOne_Left()),
            AliasedEntity(_EntityGraphBuilder_ManyToOne_Right()),
        ),
    ])
    async def test_build_many_to_one(
        self,
        many_to_one_left: AliasableEntity[_EntityGraphBuilder_ManyToOne_Left],
        many_to_one_right: AliasableEntity[_EntityGraphBuilder_ManyToOne_Right],
    ) -> None:
        sut = EntityGraphBuilder()
        sut.add_entity(many_to_one_left, many_to_one_right)  # type: ignore[arg-type]
        sut.add_association(
            _EntityGraphBuilder_ManyToOne_Left,
            many_to_one_left.id,
            'to_one',
            _EntityGraphBuilder_ManyToOne_Right,
            many_to_one_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_many_to_one_left = unalias(many_to_one_left)
        unaliased_many_to_one_right = unalias(many_to_one_right)

        assert unaliased_many_to_one_left is built_entities[_EntityGraphBuilder_ManyToOne_Left][unaliased_many_to_one_left.id]
        assert unaliased_many_to_one_right is built_entities[_EntityGraphBuilder_ManyToOne_Right][unaliased_many_to_one_right.id]
        assert unaliased_many_to_one_right is unaliased_many_to_one_left.to_one
        assert unaliased_many_to_one_left in unaliased_many_to_one_right.to_many

    @pytest.mark.parametrize('to_many_left, to_many_right', [
        (
            _EntityGraphBuilder_ToMany_Left(),
            _EntityGraphBuilder_ToMany_Right(),
        ),
        (
            AliasedEntity(_EntityGraphBuilder_ToMany_Left()),
            AliasedEntity(_EntityGraphBuilder_ToMany_Right()),
        ),
    ])
    async def test_build_to_many(
        self,
        to_many_left: AliasableEntity[_EntityGraphBuilder_ToMany_Left],
        to_many_right: AliasableEntity[_EntityGraphBuilder_ToMany_Right],
    ) -> None:
        sut = EntityGraphBuilder()
        sut.add_entity(to_many_left, to_many_right)  # type: ignore[arg-type]
        sut.add_association(
            _EntityGraphBuilder_ToMany_Left,
            to_many_left.id,
            'to_many',
            _EntityGraphBuilder_ToMany_Right,
            to_many_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_to_many_left = unalias(to_many_left)
        unaliased_to_many_right = unalias(to_many_right)

        assert unaliased_to_many_left is built_entities[_EntityGraphBuilder_ToMany_Left][unaliased_to_many_left.id]
        assert unaliased_to_many_right is built_entities[_EntityGraphBuilder_ToMany_Right][unaliased_to_many_right.id]
        assert unaliased_to_many_right in unaliased_to_many_left.to_many

    @pytest.mark.parametrize('one_to_many_left, one_to_many_right', [
        (
            _EntityGraphBuilder_OneToMany_Left(),
            _EntityGraphBuilder_OneToMany_Right(),
        ),
        (
            AliasedEntity(_EntityGraphBuilder_OneToMany_Left()),
            AliasedEntity(_EntityGraphBuilder_OneToMany_Right()),
        ),
    ])
    async def test_build_one_to_many(
        self,
        one_to_many_left: AliasableEntity[_EntityGraphBuilder_OneToMany_Left],
        one_to_many_right: AliasableEntity[_EntityGraphBuilder_OneToMany_Right],
    ) -> None:
        sut = EntityGraphBuilder()
        sut.add_entity(one_to_many_left, one_to_many_right)  # type: ignore[arg-type]
        sut.add_association(
            _EntityGraphBuilder_OneToMany_Left,
            one_to_many_left.id,
            'to_many',
            _EntityGraphBuilder_OneToMany_Right,
            one_to_many_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_one_to_many_left = unalias(one_to_many_left)
        unaliased_one_to_many_right = unalias(one_to_many_right)

        assert unaliased_one_to_many_left is built_entities[_EntityGraphBuilder_OneToMany_Left][unaliased_one_to_many_left.id]
        assert unaliased_one_to_many_right is built_entities[_EntityGraphBuilder_OneToMany_Right][unaliased_one_to_many_right.id]
        assert unaliased_one_to_many_right in unaliased_one_to_many_left.to_many
        assert unaliased_one_to_many_left is unaliased_one_to_many_right.to_one

    @pytest.mark.parametrize('many_to_many_left, many_to_many_right', [
        (
            _EntityGraphBuilder_ManyToMany_Left(),
            _EntityGraphBuilder_ManyToMany_Right(),
        ),
        (
            AliasedEntity(_EntityGraphBuilder_ManyToMany_Left()),
            AliasedEntity(_EntityGraphBuilder_ManyToMany_Right()),
        ),
    ])
    async def test_build_many_to_many(
        self,
        many_to_many_left: AliasableEntity[_EntityGraphBuilder_ManyToMany_Left],
        many_to_many_right: AliasableEntity[_EntityGraphBuilder_ManyToMany_Right],
    ) -> None:
        sut = EntityGraphBuilder()
        sut.add_entity(many_to_many_left, many_to_many_right)  # type: ignore[arg-type]
        sut.add_association(
            _EntityGraphBuilder_ManyToMany_Left,
            many_to_many_left.id,
            'to_many',
            _EntityGraphBuilder_ManyToMany_Right,
            many_to_many_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_many_to_many_left = unalias(many_to_many_left)
        unaliased_many_to_many_right = unalias(many_to_many_right)

        assert unaliased_many_to_many_left is built_entities[_EntityGraphBuilder_ManyToMany_Left][unaliased_many_to_many_left.id]
        assert unaliased_many_to_many_right is built_entities[_EntityGraphBuilder_ManyToMany_Right][unaliased_many_to_many_right.id]
        assert unaliased_many_to_many_right in unaliased_many_to_many_left.to_many
        assert unaliased_many_to_many_left in unaliased_many_to_many_right.to_many

    @pytest.mark.parametrize('many_to_one_to_many_left, many_to_one_to_many_middle, many_to_one_to_many_right', [
        (
            _EntityGraphBuilder_ManyToOneToMany_Left(),
            _EntityGraphBuilder_ManyToOneToMany_Middle(),
            _EntityGraphBuilder_ManyToOneToMany_Right(),
        ),
        (
            AliasedEntity(_EntityGraphBuilder_ManyToOneToMany_Left()),
            AliasedEntity(_EntityGraphBuilder_ManyToOneToMany_Middle()),
            AliasedEntity(_EntityGraphBuilder_ManyToOneToMany_Right()),
        ),
    ])
    async def test_build_many_to_one_to_many(
        self,
        many_to_one_to_many_left: AliasableEntity[_EntityGraphBuilder_ManyToOneToMany_Left],
        many_to_one_to_many_middle: AliasableEntity[_EntityGraphBuilder_ManyToOneToMany_Middle],
        many_to_one_to_many_right: AliasableEntity[_EntityGraphBuilder_ManyToOneToMany_Right],
    ) -> None:
        sut = EntityGraphBuilder()
        sut.add_entity(many_to_one_to_many_left, many_to_one_to_many_middle, many_to_one_to_many_right)  # type: ignore[arg-type]
        sut.add_association(
            _EntityGraphBuilder_ManyToOneToMany_Left,
            many_to_one_to_many_left.id,
            'to_many',
            _EntityGraphBuilder_ManyToOneToMany_Middle,
            many_to_one_to_many_middle.id,
        )
        sut.add_association(
            _EntityGraphBuilder_ManyToOneToMany_Right,
            many_to_one_to_many_right.id,
            'to_many',
            _EntityGraphBuilder_ManyToOneToMany_Middle,
            many_to_one_to_many_middle.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_many_to_one_to_many_left = unalias(many_to_one_to_many_left)
        unaliased_many_to_one_to_many_middle = unalias(many_to_one_to_many_middle)
        unaliased_many_to_one_to_many_right = unalias(many_to_one_to_many_right)

        assert unaliased_many_to_one_to_many_left is built_entities[_EntityGraphBuilder_ManyToOneToMany_Left][unaliased_many_to_one_to_many_left.id]
        assert unaliased_many_to_one_to_many_right is built_entities[_EntityGraphBuilder_ManyToOneToMany_Right][unaliased_many_to_one_to_many_right.id]
        assert unaliased_many_to_one_to_many_middle in unaliased_many_to_one_to_many_left.to_many
        assert unaliased_many_to_one_to_many_left == unaliased_many_to_one_to_many_middle.to_one_left
        assert unaliased_many_to_one_to_many_right == unaliased_many_to_one_to_many_middle.to_one_right
        assert unaliased_many_to_one_to_many_middle in unaliased_many_to_one_to_many_right.to_many


class TestPickleableEntityGraph:
    async def test_pickle_to_one(self) -> None:
        to_one_left = _EntityGraphBuilder_ToOne_Left()
        to_one_right = _EntityGraphBuilder_ToOne_Right()
        to_one_left.to_one = to_one_right

        sut = PickleableEntityGraph(to_one_left, to_one_right)

        unpickled_entities = MultipleTypesEntityCollection[Entity]()
        unpickled_entities.add(*dill.loads(dill.dumps(sut)).build())

        assert to_one_left is not unpickled_entities[_EntityGraphBuilder_ToOne_Left][to_one_left.id]
        assert to_one_left == unpickled_entities[_EntityGraphBuilder_ToOne_Left][to_one_left.id]
        assert to_one_right is not unpickled_entities[_EntityGraphBuilder_ToOne_Right][to_one_right.id]
        assert to_one_right == unpickled_entities[_EntityGraphBuilder_ToOne_Right][to_one_right.id]
        assert to_one_right == to_one_left.to_one

    async def test_pickle_one_to_one(self) -> None:
        one_to_one_left = _EntityGraphBuilder_OneToOne_Left()
        one_to_one_right = _EntityGraphBuilder_OneToOne_Right()
        one_to_one_left.to_one = one_to_one_right

        sut = PickleableEntityGraph(one_to_one_left, one_to_one_right)

        unpickled_entities = MultipleTypesEntityCollection[Entity]()
        unpickled_entities.add(*dill.loads(dill.dumps(sut)).build())

        assert one_to_one_left is not unpickled_entities[_EntityGraphBuilder_OneToOne_Left][one_to_one_left.id]
        assert one_to_one_left == unpickled_entities[_EntityGraphBuilder_OneToOne_Left][one_to_one_left.id]
        assert one_to_one_right is not unpickled_entities[_EntityGraphBuilder_OneToOne_Right][one_to_one_right.id]
        assert one_to_one_right == unpickled_entities[_EntityGraphBuilder_OneToOne_Right][one_to_one_right.id]
        assert one_to_one_right == one_to_one_left.to_one
        assert one_to_one_left == one_to_one_right.to_one

    async def test_pickle_many_to_one(self) -> None:
        many_to_one_left = _EntityGraphBuilder_ManyToOne_Left()
        many_to_one_right = _EntityGraphBuilder_ManyToOne_Right()
        many_to_one_left.to_one = many_to_one_right

        sut = PickleableEntityGraph(many_to_one_left, many_to_one_right)

        unpickled_entities = MultipleTypesEntityCollection[Entity]()
        unpickled_entities.add(*dill.loads(dill.dumps(sut)).build())

        assert many_to_one_left is not unpickled_entities[_EntityGraphBuilder_ManyToOne_Left][many_to_one_left.id]
        assert many_to_one_left == unpickled_entities[_EntityGraphBuilder_ManyToOne_Left][many_to_one_left.id]
        assert many_to_one_right is not unpickled_entities[_EntityGraphBuilder_ManyToOne_Right][many_to_one_right.id]
        assert many_to_one_right == unpickled_entities[_EntityGraphBuilder_ManyToOne_Right][many_to_one_right.id]
        assert many_to_one_right == many_to_one_left.to_one
        assert many_to_one_left in many_to_one_right.to_many

    async def test_pickle_to_many(self) -> None:
        to_many_left = _EntityGraphBuilder_ToMany_Left()
        to_many_right = _EntityGraphBuilder_ToMany_Right()
        to_many_left.to_many = [to_many_right]  # type: ignore[assignment]

        sut = PickleableEntityGraph(to_many_left, to_many_right)

        unpickled_entities = MultipleTypesEntityCollection[Entity]()
        unpickled_entities.add(*dill.loads(dill.dumps(sut)).build())

        assert to_many_left is not unpickled_entities[_EntityGraphBuilder_ToMany_Left][to_many_left.id]
        assert to_many_left == unpickled_entities[_EntityGraphBuilder_ToMany_Left][to_many_left.id]
        assert to_many_right is not unpickled_entities[_EntityGraphBuilder_ToMany_Right][to_many_right.id]
        assert to_many_right == unpickled_entities[_EntityGraphBuilder_ToMany_Right][to_many_right.id]
        assert to_many_right in to_many_left.to_many

    async def test_pickle_one_to_many(self) -> None:
        one_to_many_left = _EntityGraphBuilder_OneToMany_Left()
        one_to_many_right = _EntityGraphBuilder_OneToMany_Right()
        one_to_many_left.to_many = [one_to_many_right]  # type: ignore[assignment]

        sut = PickleableEntityGraph(one_to_many_left, one_to_many_right)

        unpickled_entities = MultipleTypesEntityCollection[Entity]()
        unpickled_entities.add(*dill.loads(dill.dumps(sut)).build())

        assert one_to_many_left is not unpickled_entities[_EntityGraphBuilder_OneToMany_Left][one_to_many_left.id]
        assert one_to_many_left == unpickled_entities[_EntityGraphBuilder_OneToMany_Left][one_to_many_left.id]
        assert one_to_many_right is not unpickled_entities[_EntityGraphBuilder_OneToMany_Right][one_to_many_right.id]
        assert one_to_many_right == unpickled_entities[_EntityGraphBuilder_OneToMany_Right][one_to_many_right.id]
        assert one_to_many_right in one_to_many_left.to_many
        assert one_to_many_left == one_to_many_right.to_one

    async def test_pickle_many_to_many(self) -> None:
        many_to_many_left = _EntityGraphBuilder_ManyToMany_Left()
        many_to_many_right = _EntityGraphBuilder_ManyToMany_Right()
        many_to_many_left.to_many = [many_to_many_right]  # type: ignore[assignment]

        sut = PickleableEntityGraph(many_to_many_left, many_to_many_right)

        unpickled_entities = MultipleTypesEntityCollection[Entity]()
        unpickled_entities.add(*dill.loads(dill.dumps(sut)).build())

        assert many_to_many_left is not unpickled_entities[_EntityGraphBuilder_ManyToMany_Left][many_to_many_left.id]
        assert many_to_many_left == unpickled_entities[_EntityGraphBuilder_ManyToMany_Left][many_to_many_left.id]
        assert many_to_many_right is not unpickled_entities[_EntityGraphBuilder_ManyToMany_Right][many_to_many_right.id]
        assert many_to_many_right == unpickled_entities[_EntityGraphBuilder_ManyToMany_Right][many_to_many_right.id]
        assert many_to_many_right in many_to_many_left.to_many
        assert many_to_many_left in many_to_many_right.to_many

    async def test_pickle_many_to_one_to_many(self) -> None:
        many_to_one_to_many_left = _EntityGraphBuilder_ManyToOneToMany_Left()
        many_to_one_to_many_middle = _EntityGraphBuilder_ManyToOneToMany_Middle()
        many_to_one_to_many_right = _EntityGraphBuilder_ManyToOneToMany_Right()
        many_to_one_to_many_left.to_many = [many_to_one_to_many_middle]  # type: ignore[assignment]
        many_to_one_to_many_right.to_many = [many_to_one_to_many_middle]  # type: ignore[assignment]

        sut = PickleableEntityGraph(many_to_one_to_many_left, many_to_one_to_many_middle, many_to_one_to_many_right)

        unpickled_entities = MultipleTypesEntityCollection[Entity]()
        unpickled_entities.add(*dill.loads(dill.dumps(sut)).build())

        assert many_to_one_to_many_left is not unpickled_entities[_EntityGraphBuilder_ManyToOneToMany_Left][many_to_one_to_many_left.id]
        assert many_to_one_to_many_left == unpickled_entities[_EntityGraphBuilder_ManyToOneToMany_Left][many_to_one_to_many_left.id]
        assert many_to_one_to_many_middle is not unpickled_entities[_EntityGraphBuilder_ManyToOneToMany_Middle][many_to_one_to_many_middle.id]
        assert many_to_one_to_many_middle == unpickled_entities[_EntityGraphBuilder_ManyToOneToMany_Middle][many_to_one_to_many_middle.id]
        assert many_to_one_to_many_right is not unpickled_entities[_EntityGraphBuilder_ManyToOneToMany_Right][many_to_one_to_many_right.id]
        assert many_to_one_to_many_right == unpickled_entities[_EntityGraphBuilder_ManyToOneToMany_Right][many_to_one_to_many_right.id]
        assert many_to_one_to_many_middle in many_to_one_to_many_left.to_many
        assert many_to_one_to_many_left == many_to_one_to_many_middle.to_one_left
        assert many_to_one_to_many_right == many_to_one_to_many_middle.to_one_right
        assert many_to_one_to_many_middle in many_to_one_to_many_right.to_many


@to_one(
    'one',
    'betty.tests.model.test___init__._TestToOne_One',
)
class _TestToOne_Some(Entity):
    one: _TestToOne_One | None


class _TestToOne_One(Entity):
    pass


class TestToOne:
    async def test(self) -> None:
        assert {'one'} == {
            association.owner_attr_name
            for association
            in EntityTypeAssociationRegistry.get_all_associations(_TestToOne_Some)
        }

        entity_some = _TestToOne_Some()
        entity_one = _TestToOne_One()

        entity_some.one = entity_one
        assert entity_one is entity_some.one

        del entity_some.one
        assert entity_some.one is None


@one_to_one(
    'other_one',
    'betty.tests.model.test___init__._TestOneToOne_OtherOne',
    'one',
)
class _TestOneToOne_One(Entity):
    other_one: _TestOneToOne_OtherOne | None


@one_to_one(
    'one',
    'betty.tests.model.test___init__._TestOneToOne_One',
    'other_one',
)
class _TestOneToOne_OtherOne(Entity):
    one: _TestOneToOne_One | None


class TestOneToOne:
    async def test(self) -> None:
        assert {'one'} == {
            association.owner_attr_name
            for association
            in EntityTypeAssociationRegistry.get_all_associations(_TestOneToOne_OtherOne)
        }

        entity_one = _TestOneToOne_One()
        entity_other_one = _TestOneToOne_OtherOne()

        entity_other_one.one = entity_one
        assert entity_one is entity_other_one.one
        assert entity_other_one == entity_one.other_one

        del entity_other_one.one
        assert entity_other_one.one is None
        assert entity_one.other_one is None


@many_to_one(
    'one',
    'betty.tests.model.test___init__._TestManyToOne_One',
    'many',
)
class _TestManyToOne_Many(Entity):
    one: _TestManyToOne_One | None


@one_to_many(
    'many',
    'betty.tests.model.test___init__._TestManyToOne_Many',
    'one',
)
class _TestManyToOne_One(Entity):
    many: EntityCollection[_TestManyToOne_Many]


class TestManyToOne:
    async def test(self) -> None:
        assert {'one'} == {
            association.owner_attr_name
            for association
            in EntityTypeAssociationRegistry.get_all_associations(_TestManyToOne_Many)
        }

        entity_many = _TestManyToOne_Many()
        entity_one = _TestManyToOne_One()

        entity_many.one = entity_one
        assert entity_one is entity_many.one
        assert [entity_many] == list(entity_one.many)

        del entity_many.one
        assert entity_many.one is None
        assert [] == list(entity_one.many)


@to_many(
    'many',
    'betty.tests.model.test___init__._TestToMany_Many',
)
class _TestToMany_One(Entity):
    many: EntityCollection[_TestToMany_Many]


class _TestToMany_Many(Entity):
    pass


class TestToMany:
    async def test(self) -> None:
        assert {'many'} == {
            association.owner_attr_name
            for association
            in EntityTypeAssociationRegistry.get_all_associations(_TestToMany_One)
        }

        entity_one = _TestToMany_One()
        entity_many = _TestToMany_Many()

        entity_one.many.add(entity_many)
        assert [entity_many] == list(entity_one.many)

        entity_one.many.remove(entity_many)
        assert [] == list(entity_one.many)


@one_to_many(
    'many',
    'betty.tests.model.test___init__._TestOneToMany_Many',
    'one',
)
class _TestOneToMany_One(Entity):
    many: SingleTypeEntityCollection[_TestOneToMany_Many]


@many_to_one(
    'one',
    'betty.tests.model.test___init__._TestOneToMany_One',
    'many',
)
class _TestOneToMany_Many(Entity):
    one: _TestOneToMany_One | None


class TestOneToMany:
    async def test(self) -> None:
        assert {'many'} == {
            association.owner_attr_name
            for association
            in EntityTypeAssociationRegistry.get_all_associations(_TestOneToMany_One)
        }

        entity_one = _TestOneToMany_One()
        entity_many = _TestOneToMany_Many()

        entity_one.many.add(entity_many)
        assert [entity_many] == list(entity_one.many)
        assert entity_one is entity_many.one

        entity_one.many.remove(entity_many)
        assert [] == list(entity_one.many)
        assert entity_many.one is None


@many_to_many(
    'other_many',
    'betty.tests.model.test___init__._TestManyToMany_OtherMany',
    'many',
)
class _TestManyToMany_Many(Entity):
    other_many: EntityCollection[_TestManyToMany_OtherMany]


@many_to_many(
    'many',
    'betty.tests.model.test___init__._TestManyToMany_Many',
    'other_many',
)
class _TestManyToMany_OtherMany(Entity):
    many: EntityCollection[_TestManyToMany_Many]


class TestManyToMany:
    async def test(self) -> None:
        assert {'other_many'} == {
            association.owner_attr_name
            for association
            in EntityTypeAssociationRegistry.get_all_associations(_TestManyToMany_Many)
        }

        entity_many = _TestManyToMany_Many()
        entity_other_many = _TestManyToMany_OtherMany()

        entity_many.other_many.add(entity_other_many)
        assert [entity_other_many] == list(entity_many.other_many)
        assert [entity_many] == list(entity_other_many.many)

        entity_many.other_many.remove(entity_other_many)
        assert [] == list(entity_many.other_many)
        assert [] == list(entity_other_many.many)


@many_to_one_to_many(
    'betty.tests.model.test___init__._TestManyToOneToMany_Left',
    'one',
    'left_many',
    'right_many',
    'betty.tests.model.test___init__._TestManyToOneToMany_Right',
    'one',
)
class _TestManyToOneToMany_Middle(Entity):
    left_many: _TestManyToOneToMany_Left | None
    right_many: _TestManyToOneToMany_Right | None


@one_to_many(
    'one',
    'betty.tests.model.test___init__._TestManyToOneToMany_Middle',
    'left_many',
)
class _TestManyToOneToMany_Left(Entity):
    one: EntityCollection[_TestManyToOneToMany_Middle]


@one_to_many(
    'one',
    'betty.tests.model.test___init__._TestManyToOneToMany_Middle',
    'right_many',
)
class _TestManyToOneToMany_Right(Entity):
    one: EntityCollection[_TestManyToOneToMany_Middle]


class TestManyToOneToMany:
    async def test(self) -> None:
        assert {'left_many', 'right_many'} == {
            association.owner_attr_name
            for association
            in EntityTypeAssociationRegistry.get_all_associations(_TestManyToOneToMany_Middle)
        }

        entity_one = _TestManyToOneToMany_Middle()
        entity_left_many = _TestManyToOneToMany_Left()
        entity_right_many = _TestManyToOneToMany_Right()

        entity_one.left_many = entity_left_many
        assert entity_left_many is entity_one.left_many
        assert [entity_one] == list(entity_left_many.one)

        entity_one.right_many = entity_right_many
        assert entity_right_many is entity_one.right_many
        assert [entity_one] == list(entity_right_many.one)
