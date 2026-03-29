from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.entity.collection.multiple import MultipleTypesEntityCollection
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.entity.collection import EntityCollectionTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.entity.collection import EntityCollection


class TestMultipleTypesEntityCollection(EntityCollectionTestBase[DummyEntityOne]):
    @override
    @pytest.fixture
    def sut(self) -> EntityCollection[DummyEntityOne]:
        return MultipleTypesEntityCollection()

    @override
    @pytest.fixture
    def sut_entities(self) -> Sequence[DummyEntityOne]:
        return DummyEntityOne(), DummyEntityOne(), DummyEntityOne()

    def test___getitem____by_entity_type(
        self,
        sut: MultipleTypesEntityCollection[DummyEntityOne],
        sut_entities: Sequence[DummyEntityOne],
    ) -> None:
        sut.add(*sut_entities)
        assert list(sut[DummyEntityOne]) == list(sut_entities)

    def test___getitem____by_entity_type_id(
        self,
        sut: MultipleTypesEntityCollection[DummyEntityOne],
        sut_entities: Sequence[DummyEntityOne],
    ) -> None:
        sut.add(*sut_entities)
        assert list(sut[DummyEntityOne.plugin().id]) == list(sut_entities)

    def test___delitem__(
        self,
        sut: MultipleTypesEntityCollection[DummyEntityOne],
        sut_entities: Sequence[DummyEntityOne],
    ) -> None:
        sut.add(*sut_entities)

        del sut[sut_entities[0]]

        assert list(sut) == list(sut_entities[1:])
