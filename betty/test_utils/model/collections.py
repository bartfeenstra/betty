"""
Test utilities for :py:mod:`betty.model.collections`.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

import pytest

from betty.model import Entity
from betty.model.collections import EntityCollection

_EntityT = TypeVar("_EntityT", bound=Entity)
_EntityCollectionT = TypeVar("_EntityCollectionT", bound=EntityCollection[Entity])


class EntityCollectionTestBase(Generic[_EntityT]):
    """
    A base class for testing :py:class:`betty.model.collections.EntityCollection` implementations.
    """

    @pytest.fixture
    def sut(self) -> EntityCollection[_EntityT]:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    @pytest.fixture
    async def sut_entities(self) -> Sequence[_EntityT]:
        """
        Produce entities to test the collections with.

        This MUST return at least 3 entities.
        """
        raise NotImplementedError

    async def test_entity_collection_test_base_sut_entities(
        self, sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.test_utils.model.collections.EntityCollectionTestBase.sut_entities` implementations.
        """
        assert len(sut_entities) >= 3

    async def test_add(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.add` implementations.
        """
        sut.add(*sut_entities)
        assert list(sut) == list(sut_entities)

    async def test_add_with_duplicate_entities(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.add` implementations.
        """
        sut.add(sut_entities[0], sut_entities[1], sut_entities[0], sut_entities[2])
        assert list(sut) == list(sut_entities[0:3])

    async def test_remove(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.remove` implementations.
        """
        sut.add(*sut_entities)
        first = sut_entities[0]
        sut.add(*sut_entities)
        sut.remove(first)
        assert list(sut) == list(sut_entities[1:])
        sut.remove(*sut_entities)
        assert list(sut) == []

    async def test___delitem____by_entity(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__delitem__` implementations.
        """
        sut.add(*sut_entities)
        first = sut_entities[0]
        sut.add(*sut_entities)
        del sut[first]
        assert list(sut) == list(sut_entities[1:])

    async def test___contains____by_entity(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__contains__` implementations.
        """
        sut.add(sut_entities[0])
        assert sut_entities[0] in sut
        assert sut_entities[1] not in sut

    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            [],
        ],
    )
    async def test___contains____by_unsupported_type(
        self, value: Any, sut: EntityCollection[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__contains__` implementations.
        """
        assert value not in sut

    async def test___len__(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__len__` implementations.
        """
        assert len(sut) == 0
        sut.add(*sut_entities)
        assert len(sut) == len(sut_entities)

    async def test___iter__(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__iter__` implementations.
        """
        assert list(iter(sut)) == []
        sut.add(*sut_entities)
        assert list(iter(sut)) == list(sut_entities)

    async def test_clear(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__iter__` implementations.
        """
        sut.add(*sut_entities)
        sut.clear()
        assert list(sut) == []

    async def test_replace(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.replace` implementations.
        """
        first = sut_entities[0]
        others = sut_entities[1:]
        sut.add(first)
        sut.replace(*others)
        assert list(sut) == list(others)

    async def test_get_mutables(
        self, sut: EntityCollection[_EntityT], sut_entities: Sequence[_EntityT]
    ) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.get_mutables` implementations.
        """
        sut.add(*sut_entities)
        sut.immutable = True
        for entity in sut_entities:
            assert entity.immutable
