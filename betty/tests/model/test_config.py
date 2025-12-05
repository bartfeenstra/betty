from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.model import EntityPlugin
from betty.model.config import EntityReference, EntityReferenceSequence
from betty.plugin.repository.static import StaticPluginRepository
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.model import (
    DummyEntityFour,
    DummyEntityOne,
    DummyEntityThree,
    DummyEntityTwo,
)

if TYPE_CHECKING:
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseNewSut,
        ConfigurationCollectionTestBaseSutConfigurations,
    )


class TestEntityReference:
    async def test_entity_type(self) -> None:
        entity_type = DummyEntityOne.plugin.id
        sut = EntityReference(entity_type, "123")
        assert sut.entity_type == entity_type

    async def test_entity_id(self) -> None:
        entity_id = "123"
        sut = EntityReference(DummyEntityOne, entity_id)
        assert sut.entity_id == entity_id

    async def test_load(self) -> None:
        entity_type = DummyEntityOne.plugin.id
        entity_id = "123"
        sut = EntityReference.load(
            {
                "type": entity_type,
                "id": entity_id,
            }
        )
        assert sut.entity_type == entity_type
        assert sut.entity_id == entity_id

    async def test_load__without_entity_type(self) -> None:
        with pytest.raises(HumanFacingException):
            EntityReference.load(
                {
                    "id": "123",
                }
            )

    async def test_load__without_entity_id(self) -> None:
        with pytest.raises(HumanFacingException):
            EntityReference.load(
                {
                    "type": DummyEntityOne.plugin.id,
                }
            )

    async def test_dump(self) -> None:
        entity_type = DummyEntityOne.plugin
        entity_id = "123"
        sut = EntityReference(entity_type, entity_id)
        sut.entity_type = entity_type.id
        sut.entity_id = entity_id
        expected = {
            "type": entity_type.id,
            "id": entity_id,
        }
        assert sut.dump() == expected

    async def test_validate(self) -> None:
        sut = EntityReference("betty.non_existent.Entity", "id")
        with pytest.raises(HumanFacingException):
            await sut.validate(StaticPluginRepository(EntityPlugin))


class TestEntityReferenceSequence(ConfigurationSequenceTestBase[EntityReference]):
    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[EntityReference, int, int]:
        return EntityReferenceSequence

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[EntityReference]:
        return (
            EntityReference(DummyEntityOne, "ONE"),
            EntityReference(DummyEntityTwo, "TWO"),
            EntityReference(DummyEntityThree, "THREE"),
            EntityReference(DummyEntityFour, "FOUR"),
        )

    async def test_validate__with_invalid_item(
        self,
    ) -> None:
        sut = EntityReferenceSequence(
            [EntityReference("betty.non_existent.Entity", "123")]
        )
        with pytest.raises(HumanFacingException):
            await sut.validate(StaticPluginRepository(EntityPlugin))
