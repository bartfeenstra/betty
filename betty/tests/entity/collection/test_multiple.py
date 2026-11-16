from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.entity.collection.multiple import MultipleTypesEntityCollection
from betty.test_utils.entity import (
    AnyDummyEntity,
    DummyEntityFour,
    DummyEntityOne,
    DummyEntityThree,
    DummyEntityTwo,
    DummyNonPublicFacingEntityOne,
)
from betty.test_utils.entity.collection import EntityCollectionTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.entity.collection import EntityCollection


class TestMultipleTypesEntityCollection(EntityCollectionTestBase[DummyEntityOne]):
    @override
    @pytest.fixture
    def sut(self) -> EntityCollection[AnyDummyEntity]:
        return MultipleTypesEntityCollection()

    @override
    @pytest.fixture
    def sut_entities(self) -> Sequence[AnyDummyEntity]:
        return (
            DummyEntityOne(),
            DummyEntityTwo(),
            DummyEntityThree(),
            DummyEntityFour(),
            DummyNonPublicFacingEntityOne(),
        )

    def test___getitem____by_entity_type(
        self,
        sut: MultipleTypesEntityCollection[AnyDummyEntity],
        sut_entities: Sequence[AnyDummyEntity],
    ) -> None:
        sut.add(*sut_entities)
        assert list(sut[DummyEntityOne]) == [
            entity for entity in sut_entities if isinstance(entity, DummyEntityOne)
        ]

    def test___getitem____by_entity_type_id(
        self,
        sut: MultipleTypesEntityCollection[AnyDummyEntity],
        sut_entities: Sequence[AnyDummyEntity],
    ) -> None:
        sut.add(*sut_entities)
        assert list(sut[DummyEntityOne.definition.id]) == [
            entity for entity in sut_entities if isinstance(entity, DummyEntityOne)
        ]

    def test___delitem__(
        self,
        sut: MultipleTypesEntityCollection[AnyDummyEntity],
        sut_entities: Sequence[AnyDummyEntity],
    ) -> None:
        sut.add(*sut_entities)

        del sut[sut_entities[0]]

        assert list(sut) == list(sut_entities[1:])

    def test_freeze(
        self,
        sut: MultipleTypesEntityCollection[AnyDummyEntity],
        sut_entities: Sequence[AnyDummyEntity],
    ) -> None:
        sut.add(*sut_entities)
        sut.freeze()
        for entity in sut_entities:
            assert entity.is_frozen
            assert sut[entity.definition].is_frozen
