from __future__ import annotations

from typing import Iterator, Any

import pytest

from betty.model.association import (
    ToOne,
    AssociationRegistry,
    OneToOne,
    ManyToOne,
    OneToMany,
    ToMany,
    Association,
    ManyToMany,
)
from betty.test_utils.model import DummyEntity


class TestAssociationRegistry:
    @pytest.fixture(scope="class", autouse=True)
    def associations(
        self,
    ) -> Iterator[tuple[Association[Any, Any], Association[Any, Any]]]:
        parent_association = ToOne[
            _TestAssociationRegistry_ParentEntity,
            _TestAssociationRegistry_ChildEntity,
        ](
            "betty.tests.model.test_association:_TestAssociationRegistry_ParentEntity",
            "parent_associate",
            "betty.tests.model.test_association:_TestAssociationRegistry_Associate",
        )
        AssociationRegistry._register(parent_association)
        child_association = ToOne[
            _TestAssociationRegistry_ChildEntity,
            _TestAssociationRegistry_ParentEntity,
        ](
            "betty.tests.model.test_association:_TestAssociationRegistry_ChildEntity",
            "child_associate",
            "betty.tests.model.test_association:_TestAssociationRegistry_Associate",
        )
        AssociationRegistry._register(child_association)
        yield parent_association, child_association
        AssociationRegistry._associations.remove(parent_association)
        AssociationRegistry._associations.remove(child_association)

    async def test_get_associations_with_parent_class_should_return_parent_associations(
        self,
        associations: tuple[Association[Any, Any], Association[Any, Any]],
    ) -> None:
        parent_registration, _ = associations
        assert {parent_registration} == AssociationRegistry.get_all_associations(
            _TestAssociationRegistry_ParentEntity
        )

    async def test_get_associations_with_child_class_should_return_child_associations(
        self,
        associations: tuple[Association[Any, Any], Association[Any, Any]],
    ) -> None:
        parent_association, child_association = associations
        assert {
            parent_association,
            child_association,
        } == AssociationRegistry.get_all_associations(
            _TestAssociationRegistry_ChildEntity
        )


class _TestAssociationRegistry_ParentEntity(DummyEntity):
    pass


class _TestAssociationRegistry_ChildEntity(_TestAssociationRegistry_ParentEntity):
    pass


class _TestAssociationRegistry_Associate(DummyEntity):
    pass


class _TestToOne_Some(DummyEntity):
    one = ToOne["_TestToOne_Some", "_TestToOne_One"](
        "betty.tests.model.test_association:_TestToOne_Some",
        "one",
        "betty.tests.model.test_association:_TestToOne_One",
    )


class _TestToOne_One(DummyEntity):
    pass


class TestToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(_TestToOne_Some)
        }

        entity_some = _TestToOne_Some()
        entity_one = _TestToOne_One()

        entity_some.one = entity_one
        assert entity_one is entity_some.one

        del entity_some.one
        assert entity_some.one is None


class _TestOneToOne_One(DummyEntity):
    other_one = OneToOne["_TestOneToOne_One", "_TestOneToOne_OtherOne"](
        "betty.tests.model.test_association:_TestOneToOne_One",
        "other_one",
        "betty.tests.model.test_association:_TestOneToOne_OtherOne",
        "one",
    )


class _TestOneToOne_OtherOne(DummyEntity):
    one = OneToOne["_TestOneToOne_OtherOne", _TestOneToOne_One](
        "betty.tests.model.test_association:_TestOneToOne_OtherOne",
        "one",
        "betty.tests.model.test_association:_TestOneToOne_One",
        "other_one",
    )


class TestOneToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
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


class _TestManyToOne_Many(DummyEntity):
    one = ManyToOne["_TestManyToOne_Many", "_TestManyToOne_One"](
        "betty.tests.model.test_association:_TestManyToOne_Many",
        "one",
        "betty.tests.model.test_association:_TestManyToOne_One",
        "many",
    )


class _TestManyToOne_One(DummyEntity):
    many = OneToMany["_TestManyToOne_One", _TestManyToOne_Many](
        "betty.tests.model.test_association:_TestManyToOne_One",
        "many",
        "betty.tests.model.test_association:_TestManyToOne_Many",
        "one",
    )


class TestManyToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
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


class _TestToMany_One(DummyEntity):
    many = ToMany["_TestToMany_One", "_TestToMany_Many"](
        "betty.tests.model.test_association:_TestToMany_One",
        "many",
        "betty.tests.model.test_association:_TestToMany_Many",
    )


class _TestToMany_Many(DummyEntity):
    pass


class TestToMany:
    async def test(self) -> None:
        assert {"many"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(_TestToMany_One)
        }

        entity_one = _TestToMany_One()
        entity_many = _TestToMany_Many()

        entity_one.many.add(entity_many)
        assert [entity_many] == list(entity_one.many)

        entity_one.many.remove(entity_many)
        assert list(entity_one.many) == []


class _TestOneToMany_One(DummyEntity):
    many = OneToMany["_TestOneToMany_One", "_TestOneToMany_Many"](
        "betty.tests.model.test_association:_TestOneToMany_One",
        "many",
        "betty.tests.model.test_association:_TestOneToMany_Many",
        "one",
    )


class _TestOneToMany_Many(DummyEntity):
    one = ManyToOne["_TestOneToMany_Many", _TestOneToMany_One](
        "betty.tests.model.test_association:_TestOneToMany_Many",
        "one",
        "betty.tests.model.test_association:_TestOneToMany_One",
        "many",
    )


class TestOneToMany:
    async def test(self) -> None:
        assert {"many"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
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


class _TestManyToMany_Many(DummyEntity):
    other_many = ManyToMany["_TestManyToMany_Many", "_TestManyToMany_OtherMany"](
        "betty.tests.model.test_association:_TestManyToMany_Many",
        "other_many",
        "betty.tests.model.test_association:_TestManyToMany_OtherMany",
        "many",
    )


class _TestManyToMany_OtherMany(DummyEntity):
    many = ManyToMany["_TestManyToMany_OtherMany", "_TestManyToMany_Many"](
        "betty.tests.model.test_association:_TestManyToMany_OtherMany",
        "many",
        "betty.tests.model.test_association:_TestManyToMany_Many",
        "other_many",
    )


class TestManyToMany:
    async def test(self) -> None:
        assert {"other_many"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
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
