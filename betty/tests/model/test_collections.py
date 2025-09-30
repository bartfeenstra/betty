from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.model.collections import (
    MultipleTypesEntityCollection,
    SingleTypeEntityCollection,
    UnsupportedTarget,
)
from betty.test_utils.model import DummyEntityOne
from betty.test_utils.model.collections import EntityCollectionTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestUnsupportedTarget:
    def test_new(self) -> None:
        class _Actual:
            pass

        UnsupportedTarget.new(DummyEntityOne, _Actual())


class TestSingleTypeEntityCollection(EntityCollectionTestBase[DummyEntityOne]):
    @override
    async def get_suts(self) -> Sequence[SingleTypeEntityCollection[DummyEntityOne]]:
        return (SingleTypeEntityCollection(target_type=DummyEntityOne),)

    @override
    async def get_entities(self) -> Sequence[DummyEntityOne]:
        return DummyEntityOne(), DummyEntityOne(), DummyEntityOne()

    async def test___getitem____by_entity_id(self) -> None:
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            assert sut[entities[0].id] is entities[0]
            assert sut[entities[1].id] is entities[1]
            assert sut[entities[2].id] is entities[2]

    async def test___delitem___by_entity_id(self) -> None:
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)

            del sut[entities[0].id]

            assert list(sut) == list(entities[1:])

    async def test___contains____by_entity_id(self) -> None:
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(entities[0])

            assert entities[0].id in sut
            assert entities[1].id not in sut


class TestMultipleTypesEntityCollection(EntityCollectionTestBase[DummyEntityOne]):
    @override
    async def get_suts(self) -> Sequence[MultipleTypesEntityCollection[DummyEntityOne]]:
        return (MultipleTypesEntityCollection(),)

    @override
    async def get_entities(self) -> Sequence[DummyEntityOne]:
        return DummyEntityOne(), DummyEntityOne(), DummyEntityOne()

    async def test___getitem____by_entity_type(self) -> None:
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)
            assert list(sut[DummyEntityOne]) == list(entities)

    async def test___delitem___by_entity_type(self) -> None:
        for sut in await self.get_suts():
            entities = await self.get_entities()
            sut.add(*entities)

            del sut[DummyEntityOne]

            assert list(sut) == []
