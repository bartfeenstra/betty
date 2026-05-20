from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

import pytest

from betty.associations.to_one import ToOne
from betty.entity import Entity, EntityDefinition
from betty.entity.collection.pool import EntityPool
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.entity.collection import EntityCollectionTestBase
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.entity.collection import (
        EntityCollection,
    )


@EntityDefinition(
    "left",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _TestEntityPool_OneToOne_Left(Entity):
    one_right = ToOne[Self, "_TestEntityPool_OneToOne_Right"](
        "betty.tests.entity.collection.test_pool:_TestEntityPool_OneToOne_Right",
        "one_left",
        label="-",
    ).optional


@EntityDefinition(
    "right",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _TestEntityPool_OneToOne_Right(Entity):
    one_left = ToOne[Self, _TestEntityPool_OneToOne_Left](
        "betty.tests.entity.collection.test_pool:_TestEntityPool_OneToOne_Left",
        "one_right",
        label="-",
    ).optional


class TestEntityPool(EntityCollectionTestBase[Entity]):
    @override
    @pytest.fixture
    def sut(self) -> EntityCollection:
        return EntityPool()

    @override
    @pytest.fixture
    def sut_entities(
        self,
    ) -> Sequence[Entity]:
        return (
            _TestEntityPool_OneToOne_Left(),
            _TestEntityPool_OneToOne_Right(),
            DummyEntityOne(),
        )

    def test___init___with_entities(self) -> None:
        entity = DummyEntityOne()
        sut = EntityPool(entity)
        assert entity in sut

    def test_add_(self) -> None:
        sut = EntityPool()
        left = _TestEntityPool_OneToOne_Left()
        right = _TestEntityPool_OneToOne_Right()
        left.one_right = right
        sut.add(left)
        assert left in sut
        assert right in sut

    def test_unchecked(self) -> None:
        sut = EntityPool()
        left = _TestEntityPool_OneToOne_Left()
        right = _TestEntityPool_OneToOne_Right()
        left.one_right = right
        with sut.unchecked():
            sut.add(left)
        assert left in sut
        assert right not in sut
