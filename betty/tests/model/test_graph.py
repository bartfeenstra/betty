from __future__ import annotations

import pickle

import pytest

from betty.model import AliasedEntity, AliasableEntity, Entity, unalias
from betty.model.association import (
    ToOne,
    OneToOne,
    ManyToOne,
    OneToMany,
    ToMany,
    ManyToMany,
)
from betty.model.collections import MultipleTypesEntityCollection
from betty.model.graph import EntityGraphBuilder, PickleableEntityGraph
from betty.test_utils.model import DummyEntity


class _EntityGraphBuilder_ToOne_Left(DummyEntity):
    to_one = ToOne["_EntityGraphBuilder_ToOne_Left", "_EntityGraphBuilder_ToOne_Right"](
        "betty.tests.model.test_graph:_EntityGraphBuilder_ToOne_Left",
        "to_one",
        "betty.tests.model.test_graph:_EntityGraphBuilder_ToOne_Right",
    )


class _EntityGraphBuilder_ToOne_Right(DummyEntity):
    pass


class _EntityGraphBuilder_OneToOne_Left(DummyEntity):
    to_one = OneToOne[
        "_EntityGraphBuilder_OneToOne_Left", "_EntityGraphBuilder_OneToOne_Right"
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_OneToOne_Left",
        "to_one",
        "betty.tests.model.test_graph:_EntityGraphBuilder_OneToOne_Right",
        "to_one",
    )


class _EntityGraphBuilder_OneToOne_Right(DummyEntity):
    to_one = OneToOne[
        "_EntityGraphBuilder_OneToOne_Right", _EntityGraphBuilder_OneToOne_Left
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_OneToOne_Right",
        "to_one",
        "betty.tests.model.test_graph:_EntityGraphBuilder_OneToOne_Left",
        "to_one",
    )


class _EntityGraphBuilder_ManyToOne_Left(DummyEntity):
    to_one = ManyToOne[
        "_EntityGraphBuilder_ManyToOne_Left", "_EntityGraphBuilder_ManyToOne_Right"
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_ManyToOne_Left",
        "to_one",
        "betty.tests.model.test_graph:_EntityGraphBuilder_ManyToOne_Right",
        "to_many",
    )


class _EntityGraphBuilder_ManyToOne_Right(DummyEntity):
    to_many = OneToMany[
        "_EntityGraphBuilder_ManyToOne_Right", _EntityGraphBuilder_ManyToOne_Left
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_ManyToOne_Right",
        "to_many",
        "betty.tests.model.test_graph:_EntityGraphBuilder_ManyToOne_Left",
        "to_one",
    )


class _EntityGraphBuilder_ToMany_Left(DummyEntity):
    to_many = ToMany[
        "_EntityGraphBuilder_ToMany_Left", "_EntityGraphBuilder_ToMany_Right"
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_ToMany_Left",
        "to_many",
        "betty.tests.model.test_graph:_EntityGraphBuilder_ToMany_Right",
    )


class _EntityGraphBuilder_ToMany_Right(DummyEntity):
    pass


class _EntityGraphBuilder_OneToMany_Left(DummyEntity):
    to_many = OneToMany[
        "_EntityGraphBuilder_OneToMany_Left", "_EntityGraphBuilder_OneToMany_Right"
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_OneToMany_Left",
        "to_many",
        "betty.tests.model.test_graph:_EntityGraphBuilder_OneToMany_Right",
        "to_one",
    )


class _EntityGraphBuilder_OneToMany_Right(DummyEntity):
    to_one = ManyToOne[
        "_EntityGraphBuilder_OneToMany_Right", _EntityGraphBuilder_OneToMany_Left
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_OneToMany_Right",
        "to_one",
        "betty.tests.model.test_graph:_EntityGraphBuilder_OneToMany_Left",
        "to_many",
    )


class _EntityGraphBuilder_ManyToMany_Left(DummyEntity):
    to_many = ManyToMany[
        "_EntityGraphBuilder_ManyToMany_Left", "_EntityGraphBuilder_ManyToMany_Right"
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_ManyToMany_Left",
        "to_many",
        "betty.tests.model.test_graph:_EntityGraphBuilder_ManyToMany_Right",
        "to_many",
    )


class _EntityGraphBuilder_ManyToMany_Right(DummyEntity):
    to_many = ManyToMany[
        "_EntityGraphBuilder_ManyToMany_Right", _EntityGraphBuilder_ManyToMany_Left
    ](
        "betty.tests.model.test_graph:_EntityGraphBuilder_ManyToMany_Right",
        "to_many",
        "betty.tests.model.test_graph:_EntityGraphBuilder_ManyToMany_Left",
        "to_many",
    )


class TestEntityGraphBuilder:
    @pytest.mark.parametrize(
        ("to_one_left", "to_one_right"),
        [
            (
                _EntityGraphBuilder_ToOne_Left(),
                _EntityGraphBuilder_ToOne_Right(),
            ),
            (
                AliasedEntity(_EntityGraphBuilder_ToOne_Left()),
                AliasedEntity(_EntityGraphBuilder_ToOne_Right()),
            ),
        ],
    )
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
            "to_one",
            _EntityGraphBuilder_ToOne_Right,
            to_one_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_to_one_left = unalias(to_one_left)
        unaliased_to_one_right = unalias(to_one_right)

        assert (
            unaliased_to_one_left
            is built_entities[_EntityGraphBuilder_ToOne_Left][unaliased_to_one_left.id]
        )
        assert (
            unaliased_to_one_right
            is built_entities[_EntityGraphBuilder_ToOne_Right][
                unaliased_to_one_right.id
            ]
        )
        assert unaliased_to_one_right is unaliased_to_one_left.to_one

    @pytest.mark.parametrize(
        ("one_to_one_left", "one_to_one_right"),
        [
            (
                _EntityGraphBuilder_OneToOne_Left(),
                _EntityGraphBuilder_OneToOne_Right(),
            ),
            (
                AliasedEntity(_EntityGraphBuilder_OneToOne_Left()),
                AliasedEntity(_EntityGraphBuilder_OneToOne_Right()),
            ),
        ],
    )
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
            "to_one",
            _EntityGraphBuilder_OneToOne_Right,
            one_to_one_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_one_to_one_left = unalias(one_to_one_left)
        unaliased_one_to_one_right = unalias(one_to_one_right)

        assert (
            unaliased_one_to_one_left
            is built_entities[_EntityGraphBuilder_OneToOne_Left][
                unaliased_one_to_one_left.id
            ]
        )
        assert (
            unaliased_one_to_one_right
            is built_entities[_EntityGraphBuilder_OneToOne_Right][
                unaliased_one_to_one_right.id
            ]
        )
        assert unaliased_one_to_one_right is unaliased_one_to_one_left.to_one
        assert unaliased_one_to_one_left is unaliased_one_to_one_right.to_one

    @pytest.mark.parametrize(
        ("many_to_one_left", "many_to_one_right"),
        [
            (
                _EntityGraphBuilder_ManyToOne_Left(),
                _EntityGraphBuilder_ManyToOne_Right(),
            ),
            (
                AliasedEntity(_EntityGraphBuilder_ManyToOne_Left()),
                AliasedEntity(_EntityGraphBuilder_ManyToOne_Right()),
            ),
        ],
    )
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
            "to_one",
            _EntityGraphBuilder_ManyToOne_Right,
            many_to_one_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_many_to_one_left = unalias(many_to_one_left)
        unaliased_many_to_one_right = unalias(many_to_one_right)

        assert (
            unaliased_many_to_one_left
            is built_entities[_EntityGraphBuilder_ManyToOne_Left][
                unaliased_many_to_one_left.id
            ]
        )
        assert (
            unaliased_many_to_one_right
            is built_entities[_EntityGraphBuilder_ManyToOne_Right][
                unaliased_many_to_one_right.id
            ]
        )
        assert unaliased_many_to_one_right is unaliased_many_to_one_left.to_one
        assert unaliased_many_to_one_left in unaliased_many_to_one_right.to_many

    @pytest.mark.parametrize(
        ("to_many_left", "to_many_right"),
        [
            (
                _EntityGraphBuilder_ToMany_Left(),
                _EntityGraphBuilder_ToMany_Right(),
            ),
            (
                AliasedEntity(_EntityGraphBuilder_ToMany_Left()),
                AliasedEntity(_EntityGraphBuilder_ToMany_Right()),
            ),
        ],
    )
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
            "to_many",
            _EntityGraphBuilder_ToMany_Right,
            to_many_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_to_many_left = unalias(to_many_left)
        unaliased_to_many_right = unalias(to_many_right)

        assert (
            unaliased_to_many_left
            is built_entities[_EntityGraphBuilder_ToMany_Left][
                unaliased_to_many_left.id
            ]
        )
        assert (
            unaliased_to_many_right
            is built_entities[_EntityGraphBuilder_ToMany_Right][
                unaliased_to_many_right.id
            ]
        )
        assert unaliased_to_many_right in unaliased_to_many_left.to_many

    @pytest.mark.parametrize(
        ("one_to_many_left", "one_to_many_right"),
        [
            (
                _EntityGraphBuilder_OneToMany_Left(),
                _EntityGraphBuilder_OneToMany_Right(),
            ),
            (
                AliasedEntity(_EntityGraphBuilder_OneToMany_Left()),
                AliasedEntity(_EntityGraphBuilder_OneToMany_Right()),
            ),
        ],
    )
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
            "to_many",
            _EntityGraphBuilder_OneToMany_Right,
            one_to_many_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_one_to_many_left = unalias(one_to_many_left)
        unaliased_one_to_many_right = unalias(one_to_many_right)

        assert (
            unaliased_one_to_many_left
            is built_entities[_EntityGraphBuilder_OneToMany_Left][
                unaliased_one_to_many_left.id
            ]
        )
        assert (
            unaliased_one_to_many_right
            is built_entities[_EntityGraphBuilder_OneToMany_Right][
                unaliased_one_to_many_right.id
            ]
        )
        assert unaliased_one_to_many_right in unaliased_one_to_many_left.to_many
        assert unaliased_one_to_many_left is unaliased_one_to_many_right.to_one

    @pytest.mark.parametrize(
        ("many_to_many_left", "many_to_many_right"),
        [
            (
                _EntityGraphBuilder_ManyToMany_Left(),
                _EntityGraphBuilder_ManyToMany_Right(),
            ),
            (
                AliasedEntity(_EntityGraphBuilder_ManyToMany_Left()),
                AliasedEntity(_EntityGraphBuilder_ManyToMany_Right()),
            ),
        ],
    )
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
            "to_many",
            _EntityGraphBuilder_ManyToMany_Right,
            many_to_many_right.id,
        )

        built_entities = MultipleTypesEntityCollection[Entity]()
        built_entities.add(*sut.build())

        unaliased_many_to_many_left = unalias(many_to_many_left)
        unaliased_many_to_many_right = unalias(many_to_many_right)

        assert (
            unaliased_many_to_many_left
            is built_entities[_EntityGraphBuilder_ManyToMany_Left][
                unaliased_many_to_many_left.id
            ]
        )
        assert (
            unaliased_many_to_many_right
            is built_entities[_EntityGraphBuilder_ManyToMany_Right][
                unaliased_many_to_many_right.id
            ]
        )
        assert unaliased_many_to_many_right in unaliased_many_to_many_left.to_many
        assert unaliased_many_to_many_left in unaliased_many_to_many_right.to_many


class TestPickleableEntityGraph:
    def test_without_entities(self) -> None:
        sut = PickleableEntityGraph()
        unpickled_entities = list(pickle.loads(pickle.dumps(sut)).build())
        assert len(unpickled_entities) == 0

    def test_with_one_entity(self) -> None:
        entity = DummyEntity()
        sut = PickleableEntityGraph(entity)
        unpickled_entities = list(pickle.loads(pickle.dumps(sut)).build())
        assert len(unpickled_entities) == 1

    def test_with_multiple_one_to_one_associated_entities(self) -> None:
        left = _EntityGraphBuilder_OneToOne_Left()
        right = _EntityGraphBuilder_OneToOne_Right()
        left.to_one = right
        sut = PickleableEntityGraph(left, right)
        unpickled_entities = list(pickle.loads(pickle.dumps(sut)).build())
        assert len(unpickled_entities) == 2
        unpickled_left, unpickled_right = unpickled_entities
        assert unpickled_left.to_one is unpickled_right
        assert unpickled_right.to_one is unpickled_left

    def test_with_multiple_many_to_many_associated_entities(self) -> None:
        left = _EntityGraphBuilder_ManyToMany_Left()
        right = _EntityGraphBuilder_ManyToMany_Right()
        left.to_many = [right]
        sut = PickleableEntityGraph(left, right)
        unpickled_entities = list(pickle.loads(pickle.dumps(sut)).build())
        assert len(unpickled_entities) == 2
        unpickled_left, unpickled_right = unpickled_entities
        assert unpickled_left in unpickled_right.to_many
        assert unpickled_right in unpickled_left.to_many
