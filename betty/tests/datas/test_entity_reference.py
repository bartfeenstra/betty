from __future__ import annotations

from typing import TYPE_CHECKING

from betty.datas.entity_reference import EntityReference
from betty.test_utils.data import DataTestBase
from betty.test_utils.entity import DummyEntityOne

if TYPE_CHECKING:
    from betty.project import Project


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

    def test___call__(self, isolated_project: Project) -> None:
        entity = DummyEntityOne(id="my-first-entity")
        sut = EntityReference(entity.plugin(), entity.id)
        isolated_project.ancestry.add(entity)
        assert sut(isolated_project) is entity
