from __future__ import annotations

from typing import Iterator, Any, TYPE_CHECKING

import pytest
from betty.model.association import (
    ToAny,
    ToOne,
    EntityTypeAssociationRegistry,
    to_one,
    one_to_one,
    many_to_one,
    one_to_many,
    to_many,
    many_to_many,
    many_to_one_to_many,
)
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from betty.model.collections import EntityCollection, SingleTypeEntityCollection


class TestEntityTypeAssociationRegistry:
    @pytest.fixture(scope="class", autouse=True)
    def associations(self) -> Iterator[tuple[ToAny[Any, Any], ToAny[Any, Any]]]:
        parent_association = ToOne[
            _TestEntityTypeAssociationRegistry_ParentEntity,
            _TestEntityTypeAssociationRegistry_ChildEntity,
        ](
            _TestEntityTypeAssociationRegistry_ParentEntity,
            "parent_associate",
            "betty.tests.model.test_association:_TestEntityTypeAssociationRegistry_Associate",
        )
        EntityTypeAssociationRegistry._register(parent_association)
        child_association = ToOne[
            _TestEntityTypeAssociationRegistry_ChildEntity,
            _TestEntityTypeAssociationRegistry_ParentEntity,
        ](
            _TestEntityTypeAssociationRegistry_ChildEntity,
            "child_associate",
            "betty.tests.model.test_association:_TestEntityTypeAssociationRegistry_Associate",
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
        assert {
            parent_registration
        } == EntityTypeAssociationRegistry.get_all_associations(
            _TestEntityTypeAssociationRegistry_ParentEntity
        )

    async def test_get_associations_with_child_class_should_return_child_associations(
        self,
        associations: tuple[ToAny[Any, Any], ToAny[Any, Any]],
    ) -> None:
        parent_association, child_association = associations
        assert {
            parent_association,
            child_association,
        } == EntityTypeAssociationRegistry.get_all_associations(
            _TestEntityTypeAssociationRegistry_ChildEntity
        )


class _TestEntityTypeAssociationRegistry_ParentEntity(DummyEntity):
    pass


class _TestEntityTypeAssociationRegistry_ChildEntity(
    _TestEntityTypeAssociationRegistry_ParentEntity
):
    pass


class _TestEntityTypeAssociationRegistry_Associate(DummyEntity):
    pass


@to_one(
    "one",
    "betty.tests.model.test_association:_TestToOne_One",
)
class _TestToOne_Some(DummyEntity):
    one: _TestToOne_One | None


class _TestToOne_One(DummyEntity):
    pass


class TestToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in EntityTypeAssociationRegistry.get_all_associations(
                _TestToOne_Some
            )
        }

        entity_some = _TestToOne_Some()
        entity_one = _TestToOne_One()

        entity_some.one = entity_one
        assert entity_one is entity_some.one

        del entity_some.one
        assert entity_some.one is None


@one_to_one(
    "other_one",
    "betty.tests.model.test_association:_TestOneToOne_OtherOne",
    "one",
)
class _TestOneToOne_One(DummyEntity):
    other_one: _TestOneToOne_OtherOne | None


@one_to_one(
    "one",
    "betty.tests.model.test_association:_TestOneToOne_One",
    "other_one",
)
class _TestOneToOne_OtherOne(DummyEntity):
    one: _TestOneToOne_One | None


class TestOneToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in EntityTypeAssociationRegistry.get_all_associations(
                _TestOneToOne_OtherOne
            )
        }

        entity_one = _TestOneToOne_One()
        entity_other_one = _TestOneToOne_OtherOne()

        entity_other_one.one = entity_one
        assert entity_one is entity_other_one.one
        assert entity_other_one == entity_one.other_one

        del entity_other_one.one
        assert entity_other_one.one is None
        assert entity_one.other_one is None  # type: ignore[unreachable]


@many_to_one(
    "one",
    "betty.tests.model.test_association:_TestManyToOne_One",
    "many",
)
class _TestManyToOne_Many(DummyEntity):
    one: _TestManyToOne_One | None


@one_to_many(
    "many",
    "betty.tests.model.test_association:_TestManyToOne_Many",
    "one",
)
class _TestManyToOne_One(DummyEntity):
    many: EntityCollection[_TestManyToOne_Many]


class TestManyToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in EntityTypeAssociationRegistry.get_all_associations(
                _TestManyToOne_Many
            )
        }

        entity_many = _TestManyToOne_Many()
        entity_one = _TestManyToOne_One()

        entity_many.one = entity_one
        assert entity_one is entity_many.one
        assert [entity_many] == list(entity_one.many)

        del entity_many.one
        assert entity_many.one is None
        assert list(entity_one.many) == []  # type: ignore[unreachable]


@to_many(
    "many",
    "betty.tests.model.test_association:_TestToMany_Many",
)
class _TestToMany_One(DummyEntity):
    many: EntityCollection[_TestToMany_Many]


class _TestToMany_Many(DummyEntity):
    pass


class TestToMany:
    async def test(self) -> None:
        assert {"many"} == {
            association.owner_attr_name
            for association in EntityTypeAssociationRegistry.get_all_associations(
                _TestToMany_One
            )
        }

        entity_one = _TestToMany_One()
        entity_many = _TestToMany_Many()

        entity_one.many.add(entity_many)
        assert [entity_many] == list(entity_one.many)

        entity_one.many.remove(entity_many)
        assert list(entity_one.many) == []


@one_to_many(
    "many",
    "betty.tests.model.test_association:_TestOneToMany_Many",
    "one",
)
class _TestOneToMany_One(DummyEntity):
    many: SingleTypeEntityCollection[_TestOneToMany_Many]


@many_to_one(
    "one",
    "betty.tests.model.test_association:_TestOneToMany_One",
    "many",
)
class _TestOneToMany_Many(DummyEntity):
    one: _TestOneToMany_One | None


class TestOneToMany:
    async def test(self) -> None:
        assert {"many"} == {
            association.owner_attr_name
            for association in EntityTypeAssociationRegistry.get_all_associations(
                _TestOneToMany_One
            )
        }

        entity_one = _TestOneToMany_One()
        entity_many = _TestOneToMany_Many()

        entity_one.many.add(entity_many)
        assert [entity_many] == list(entity_one.many)
        assert entity_one is entity_many.one

        entity_one.many.remove(entity_many)
        assert list(entity_one.many) == []
        assert entity_many.one is None


@many_to_many(
    "other_many",
    "betty.tests.model.test_association:_TestManyToMany_OtherMany",
    "many",
)
class _TestManyToMany_Many(DummyEntity):
    other_many: EntityCollection[_TestManyToMany_OtherMany]


@many_to_many(
    "many",
    "betty.tests.model.test_association:_TestManyToMany_Many",
    "other_many",
)
class _TestManyToMany_OtherMany(DummyEntity):
    many: EntityCollection[_TestManyToMany_Many]


class TestManyToMany:
    async def test(self) -> None:
        assert {"other_many"} == {
            association.owner_attr_name
            for association in EntityTypeAssociationRegistry.get_all_associations(
                _TestManyToMany_Many
            )
        }

        entity_many = _TestManyToMany_Many()
        entity_other_many = _TestManyToMany_OtherMany()

        entity_many.other_many.add(entity_other_many)
        assert [entity_other_many] == list(entity_many.other_many)
        assert [entity_many] == list(entity_other_many.many)

        entity_many.other_many.remove(entity_other_many)
        assert list(entity_many.other_many) == []
        assert list(entity_other_many.many) == []


@many_to_one_to_many(
    "betty.tests.model.test_association:_TestManyToOneToMany_Left",
    "one",
    "left_many",
    "right_many",
    "betty.tests.model.test_association:_TestManyToOneToMany_Right",
    "one",
)
class _TestManyToOneToMany_Middle(DummyEntity):
    left_many: _TestManyToOneToMany_Left | None
    right_many: _TestManyToOneToMany_Right | None


@one_to_many(
    "one",
    "betty.tests.model.test_association:_TestManyToOneToMany_Middle",
    "left_many",
)
class _TestManyToOneToMany_Left(DummyEntity):
    one: EntityCollection[_TestManyToOneToMany_Middle]


@one_to_many(
    "one",
    "betty.tests.model.test_association:_TestManyToOneToMany_Middle",
    "right_many",
)
class _TestManyToOneToMany_Right(DummyEntity):
    one: EntityCollection[_TestManyToOneToMany_Middle]


class TestManyToOneToMany:
    async def test(self) -> None:
        assert {"left_many", "right_many"} == {
            association.owner_attr_name
            for association in EntityTypeAssociationRegistry.get_all_associations(
                _TestManyToOneToMany_Middle
            )
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
