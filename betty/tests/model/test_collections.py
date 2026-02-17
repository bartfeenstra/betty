from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.model.collections import (
    EntityCollection,
    MultipleTypesEntityCollection,
    SingleTypeEntityCollection,
)
from betty.test_utils.model import DummyEntityOne
from betty.test_utils.model.collections import EntityCollectionTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestSingleTypeEntityCollection(EntityCollectionTestBase[DummyEntityOne]):
    @override
    @pytest.fixture
    def sut(self) -> EntityCollection[DummyEntityOne]:
        return SingleTypeEntityCollection()

    @override
    @pytest.fixture
    def sut_entities(self) -> Sequence[DummyEntityOne]:
        return DummyEntityOne(), DummyEntityOne(), DummyEntityOne()

    def test___getitem____by_entity_id(
        self,
        sut: SingleTypeEntityCollection[DummyEntityOne],
        sut_entities: Sequence[DummyEntityOne],
    ) -> None:
        sut.add(*sut_entities)
        assert sut[sut_entities[0].id] is sut_entities[0]
        assert sut[sut_entities[1].id] is sut_entities[1]
        assert sut[sut_entities[2].id] is sut_entities[2]

    def test___delitem___by_entity_id(
        self,
        sut: SingleTypeEntityCollection[DummyEntityOne],
        sut_entities: Sequence[DummyEntityOne],
    ) -> None:
        sut.add(*sut_entities)

        del sut[sut_entities[0].id]

        assert list(sut) == list(sut_entities[1:])

    def test___contains____by_entity_id(
        self,
        sut: SingleTypeEntityCollection[DummyEntityOne],
        sut_entities: Sequence[DummyEntityOne],
    ) -> None:
        sut.add(sut_entities[0])

        assert sut_entities[0].id in sut
        assert sut_entities[1].id not in sut


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
