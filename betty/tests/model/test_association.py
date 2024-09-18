from __future__ import annotations

from typing import Iterator, Any

import pytest

from betty.model.association import (
    AssociationRegistry,
    _Association,
    OptionalManyToMany,
    OptionalOneToMany,
    OptionalManyToOne,
    OptionalToMany,
    OptionalOneToOne,
    OptionalToOne,
)
from betty.test_utils.model import DummyEntity


class TestAssociationRegistry:
    @pytest.fixture(scope="class", autouse=True)
    def associations(
        self,
    ) -> Iterator[
        tuple[
            _Association[Any, Any, Any, Any],
            _Association[Any, Any, Any, Any],
        ]
    ]:
        parent_association = OptionalToOne[
            _TestAssociationRegistry_ParentEntity,
            _TestAssociationRegistry_ChildEntity,
        ](
            "betty.tests.model.test_association:_TestAssociationRegistry_ParentEntity",
            "parent_associate",
            "betty.tests.model.test_association:_TestAssociationRegistry_Associate",
        )
        AssociationRegistry._register(parent_association)
        child_association = OptionalToOne[
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
        associations: tuple[
            _Association[Any, Any, Any, Any],
            _Association[Any, Any, Any, Any],
        ],
    ) -> None:
        parent_registration, _ = associations
        assert {parent_registration} == AssociationRegistry.get_all_associations(
            _TestAssociationRegistry_ParentEntity
        )

    async def test_get_associations_with_child_class_should_return_child_associations(
        self,
        associations: tuple[
            _Association[Any, Any, Any, Any],
            _Association[Any, Any, Any, Any],
        ],
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


class _TestOptionalToOne_Some(DummyEntity):
    one = OptionalToOne["_TestOptionalToOne_Some", "_TestOptionalToOne_One"](
        "betty.tests.model.test_association:_TestOptionalToOne_Some",
        "one",
        "betty.tests.model.test_association:_TestOptionalToOne_One",
    )


class _TestOptionalToOne_One(DummyEntity):
    pass


class TestOptionalToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
                _TestOptionalToOne_Some
            )
        }

        entity_some = _TestOptionalToOne_Some()
        entity_one = _TestOptionalToOne_One()

        entity_some.one = entity_one
        assert entity_one is entity_some.one

        del entity_some.one
        assert entity_some.one is None


class _TestOptionalOneToOne_One(DummyEntity):
    other_one = OptionalOneToOne[
        "_TestOptionalOneToOne_One", "_TestOptionalOneToOne_OtherOne"
    ](
        "betty.tests.model.test_association:_TestOptionalOneToOne_One",
        "other_one",
        "betty.tests.model.test_association:_TestOptionalOneToOne_OtherOne",
        "one",
    )


class _TestOptionalOneToOne_OtherOne(DummyEntity):
    one = OptionalOneToOne["_TestOptionalOneToOne_OtherOne", _TestOptionalOneToOne_One](
        "betty.tests.model.test_association:_TestOptionalOneToOne_OtherOne",
        "one",
        "betty.tests.model.test_association:_TestOptionalOneToOne_One",
        "other_one",
    )


class TestOptionalOneToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
                _TestOptionalOneToOne_OtherOne
            )
        }

        entity_one = _TestOptionalOneToOne_One()
        entity_other_one = _TestOptionalOneToOne_OtherOne()

        entity_other_one.one = entity_one
        assert entity_one is entity_other_one.one
        assert entity_other_one == entity_one.other_one

        del entity_other_one.one
        assert entity_other_one.one is None
        assert entity_one.other_one is None  # type: ignore[unreachable]


class _TestOptionalManyToOne_Many(DummyEntity):
    one = OptionalManyToOne[
        "_TestOptionalManyToOne_Many", "_TestOptionalManyToOne_One"
    ](
        "betty.tests.model.test_association:_TestOptionalManyToOne_Many",
        "one",
        "betty.tests.model.test_association:_TestOptionalManyToOne_One",
        "many",
    )


class _TestOptionalManyToOne_One(DummyEntity):
    many = OptionalOneToMany["_TestOptionalManyToOne_One", _TestOptionalManyToOne_Many](
        "betty.tests.model.test_association:_TestOptionalManyToOne_One",
        "many",
        "betty.tests.model.test_association:_TestOptionalManyToOne_Many",
        "one",
    )


class TestOptionalManyToOne:
    async def test(self) -> None:
        assert {"one"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
                _TestOptionalManyToOne_Many
            )
        }

        entity_many = _TestOptionalManyToOne_Many()
        entity_one = _TestOptionalManyToOne_One()

        entity_many.one = entity_one
        assert entity_one is entity_many.one
        assert [entity_many] == list(entity_one.many)

        del entity_many.one
        assert entity_many.one is None
        assert list(entity_one.many) == []  # type: ignore[unreachable]


class _TestOptionalToMany_One(DummyEntity):
    many = OptionalToMany["_TestOptionalToMany_One", "_TestOptionalToMany_Many"](
        "betty.tests.model.test_association:_TestOptionalToMany_One",
        "many",
        "betty.tests.model.test_association:_TestOptionalToMany_Many",
    )


class _TestOptionalToMany_Many(DummyEntity):
    pass


class TestOptionalToMany:
    async def test(self) -> None:
        assert {"many"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
                _TestOptionalToMany_One
            )
        }

        entity_one = _TestOptionalToMany_One()
        entity_many = _TestOptionalToMany_Many()

        entity_one.many.add(entity_many)
        assert [entity_many] == list(entity_one.many)

        entity_one.many.remove(entity_many)
        assert list(entity_one.many) == []


class _TestOptionalOneToMany_One(DummyEntity):
    many = OptionalOneToMany[
        "_TestOptionalOneToMany_One", "_TestOptionalOneToMany_Many"
    ](
        "betty.tests.model.test_association:_TestOptionalOneToMany_One",
        "many",
        "betty.tests.model.test_association:_TestOptionalOneToMany_Many",
        "one",
    )


class _TestOptionalOneToMany_Many(DummyEntity):
    one = OptionalManyToOne["_TestOptionalOneToMany_Many", _TestOptionalOneToMany_One](
        "betty.tests.model.test_association:_TestOptionalOneToMany_Many",
        "one",
        "betty.tests.model.test_association:_TestOptionalOneToMany_One",
        "many",
    )


class TestOptionalOneToMany:
    async def test(self) -> None:
        assert {"many"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
                _TestOptionalOneToMany_One
            )
        }

        entity_one = _TestOptionalOneToMany_One()
        entity_many = _TestOptionalOneToMany_Many()

        entity_one.many.add(entity_many)
        assert [entity_many] == list(entity_one.many)
        assert entity_one is entity_many.one

        entity_one.many.remove(entity_many)
        assert list(entity_one.many) == []
        assert entity_many.one is None


class _TestOptionalManyToMany_Many(DummyEntity):
    other_many = OptionalManyToMany[
        "_TestOptionalManyToMany_Many", "_TestOptionalManyToMany_OtherMany"
    ](
        "betty.tests.model.test_association:_TestOptionalManyToMany_Many",
        "other_many",
        "betty.tests.model.test_association:_TestOptionalManyToMany_OtherMany",
        "many",
    )


class _TestOptionalManyToMany_OtherMany(DummyEntity):
    many = OptionalManyToMany[
        "_TestOptionalManyToMany_OtherMany", "_TestOptionalManyToMany_Many"
    ](
        "betty.tests.model.test_association:_TestOptionalManyToMany_OtherMany",
        "many",
        "betty.tests.model.test_association:_TestOptionalManyToMany_Many",
        "other_many",
    )


class TestOptionalManyToMany:
    async def test(self) -> None:
        assert {"other_many"} == {
            association.owner_attr_name
            for association in AssociationRegistry.get_all_associations(
                _TestOptionalManyToMany_Many
            )
        }

        entity_many = _TestOptionalManyToMany_Many()
        entity_other_many = _TestOptionalManyToMany_OtherMany()

        entity_many.other_many.add(entity_other_many)
        assert [entity_other_many] == list(entity_many.other_many)
        assert [entity_many] == list(entity_other_many.many)

        entity_many.other_many.remove(entity_other_many)
        assert list(entity_many.other_many) == []
        assert list(entity_other_many.many) == []
