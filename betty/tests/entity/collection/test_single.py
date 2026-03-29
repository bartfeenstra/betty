from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.entity.collection.single import SingleTypeEntityCollection
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.entity.collection import EntityCollectionTestBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.entity.collection import EntityCollection


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
