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

    async def get_suts(self) -> Sequence[EntityCollection[_EntityT]]:
        """
        Produce the (empty) collections under test.

        This MUST return at least one entity collection.
        """
        raise NotImplementedError

    async def get_entities(self) -> Sequence[_EntityT]:
        """
        Produce entities to test the collections with.

        This MUST return at least 3 entities.
        """
        raise NotImplementedError

    async def test_entity_collection_test_base_get_entities(self) -> None:
        """
        Tests :py:meth:`betty.test_utils.model.collections.EntityCollectionTestBase.get_entities` implementations.
        """
        assert len(await self.get_entities()) >= 3

    async def test_add(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.add` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            assert list(sut) == list(entities)

    async def test_add_with_duplicate_entities(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.add` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(entities[0], entities[1], entities[0], entities[2])
            assert list(sut) == list(entities[0:3])

    async def test_remove(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.remove` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            first = entities[0]
            sut.add(*entities)
            sut.remove(first)
            assert list(sut) == list(entities[1:])
            sut.remove(*entities)
            assert list(sut) == []

    async def test___delitem____by_entity(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__delitem__` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            first = entities[0]
            sut.add(*entities)
            del sut[first]
            assert list(sut) == list(entities[1:])

    async def test___contains____by_entity(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__contains__` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(entities[0])
            assert entities[0] in sut
            assert entities[1] not in sut

    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            [],
        ],
    )
    async def test___contains____by_unsupported_type(self, value: Any) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__contains__` implementations.
        """
        for sut in await self.get_suts():
            assert value not in sut

    async def test___len__(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__len__` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            assert len(sut) == 0
            sut.add(*entities)
            assert len(sut) == len(entities)

    async def test___iter__(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__iter__` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            assert list(iter(sut)) == []
            sut.add(*entities)
            assert list(iter(sut)) == list(entities)

    async def test_clear(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__iter__` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            sut.clear()
            assert list(sut) == []

    async def test_replace(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.replace` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            first = entities[0]
            others = entities[1:]
            sut.add(first)
            sut.replace(*others)
            assert list(sut) == list(others)

    async def test___getitem____by_index(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__getitem__` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            assert sut[0] == entities[0]

    async def test___getitem____by_indices(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.__getitem__` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            assert list(sut[0:1:1]) == list(entities[0:1:1])
            assert list(sut[1::1]) == list(entities[1::1])

    async def test_get_mutable_instances(self) -> None:
        """
        Tests :py:meth:`betty.model.collections.EntityCollection.get_mutable_instances` implementations.
        """
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            sut.immutable()
            for entity in entities:
                assert entity.is_immutable
