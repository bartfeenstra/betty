from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.exception import HumanFacingException
from betty.model import EntityDefinition
from betty.model.reference import EntityReference
from betty.project import Project
from betty.service.level import UNIVERSE
from betty.test_utils.data import DataTestBase
from betty.test_utils.model import DummyEntityOne

if TYPE_CHECKING:
    from betty.app import App


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

    async def test_hydrate__without_project(self) -> None:
        sut = EntityReference(DummyEntityOne, "unknown-entity")
        with (
            EntityDefinition.type().discoverer.override(DummyEntityOne),
            pytest.raises(HumanFacingException),
        ):
            await sut.hydrate(UNIVERSE)

    async def test_hydrate__with_unknown_entity_type(self, isolated_app: App) -> None:
        sut = EntityReference(DummyEntityOne, "unknown-entity")
        async with Project.new_isolated(isolated_app) as project, project:
            with pytest.raises(HumanFacingException):
                await sut.hydrate(project)

    async def test_hydrate__with_unknown_entity(self, isolated_app: App) -> None:
        sut = EntityReference(DummyEntityOne, "unknown-entity")
        async with Project.new_isolated(isolated_app) as project, project:
            with EntityDefinition.type().discoverer.override(DummyEntityOne):
                with pytest.raises(HumanFacingException):
                    await sut.hydrate(project)

    async def test_hydrate__with_known_entity(self, isolated_app: App) -> None:
        entity_id = "my-first-entity"
        sut = EntityReference(DummyEntityOne, entity_id)
        async with Project.new_isolated(isolated_app) as project:
            project.ancestry[DummyEntityOne].add(DummyEntityOne(entity_id))
            async with project:
                with EntityDefinition.type().discoverer.override(DummyEntityOne):
                    await sut.hydrate(project)
