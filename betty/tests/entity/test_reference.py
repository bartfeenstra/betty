from __future__ import annotations

from betty.entity.reference import EntityReference
from betty.test_utils.data import DataTestBase
from betty.test_utils.entity import DummyEntityOne


class TestEntityReference(DataTestBase[EntityReference]):
    sut_cls = EntityReference

    def test_type(self) -> None:
        entity_type = DummyEntityOne.plugin().id
        sut = EntityReference(entity_type, "123")
        assert sut.type == entity_type

    def test_id(self) -> None:
        entity_id = "123"
        sut = EntityReference(DummyEntityOne, entity_id)
        assert sut.id == entity_id
