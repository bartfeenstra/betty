from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.model import EntityDefinition
from betty.model.config import EntityReference, EntityReferenceSequence
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.exception import raises_error
from betty.test_utils.model import DummyEntityOne, DummyEntityTwo

if TYPE_CHECKING:
    from betty.serde.dump import Dump
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseNewSut,
        ConfigurationCollectionTestBaseSutConfigurations,
    )


class TestEntityReference:
    async def test_entity_type__with_constraint(self) -> None:
        sut = EntityReference(
            DummyEntityOne.plugin, None, entity_type_is_constrained=True
        )
        assert sut.entity_type == DummyEntityOne.plugin.id
        with pytest.raises(AttributeError):
            sut.entity_type = DummyEntityTwo  # type: ignore[assignment]

    async def test_entity_type__without_constraint(self) -> None:
        sut = EntityReference()
        assert sut.entity_type is None
        sut.entity_type = DummyEntityOne  # type: ignore[assignment]
        assert sut.entity_type == DummyEntityOne.plugin.id

    async def test_entity_type_is_constrained(self) -> None:
        sut = EntityReference(
            DummyEntityOne.plugin, None, entity_type_is_constrained=True
        )
        assert sut.entity_type_is_constrained

    async def test_entity_id(self) -> None:
        entity_id = "123"
        sut = EntityReference()
        assert sut.entity_id is None
        sut.entity_id = entity_id
        assert sut.entity_id == entity_id
        del sut.entity_id
        assert sut.entity_id is None

    async def test_load__with_constraint(self) -> None:
        sut = EntityReference(DummyEntityOne.plugin, entity_type_is_constrained=True)
        entity_id = "123"
        dump = entity_id
        sut.load(dump)
        assert sut.entity_id == entity_id

    @pytest.mark.parametrize(
        "dump",
        [
            {
                "entity_type": DummyEntityOne.plugin.id,
                "entity": "123",
            },
            {
                "entity_type": DummyEntityTwo.plugin.id,
                "entity": "123",
            },
            False,
            123,
        ],
    )
    async def test_load__with_constraint_without_string_should_error(
        self, dump: Dump
    ) -> None:
        sut = EntityReference(DummyEntityOne.plugin, entity_type_is_constrained=True)
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    async def test_load__without_constraint(self) -> None:
        entity_type = DummyEntityOne.plugin
        entity_id = "123"
        dump: Dump = {
            "entity_type": entity_type.id,
            "entity": entity_id,
        }
        sut = EntityReference()
        sut.load(dump)
        assert sut.entity_type == entity_type.id
        assert sut.entity_id == entity_id

    async def test_load__without_constraint_without_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity": entity_id,
        }
        sut = EntityReference()
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    async def test_load__without_constraint_without_string_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity_type": 123,
            "entity": entity_id,
        }
        sut = EntityReference()
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    async def test_load__without_constraint_without_string_entity_id_should_error(
        self,
    ) -> None:
        dump: Dump = {
            "entity_type": DummyEntityOne.plugin.id,
            "entity": None,
        }
        sut = EntityReference()
        with raises_error(error_type=HumanFacingException):
            sut.load(dump)

    async def test_dump__with_constraint(self) -> None:
        sut = EntityReference(
            DummyEntityOne.plugin, None, entity_type_is_constrained=True
        )
        entity_id = "123"
        sut.entity_id = entity_id
        assert sut.dump() == entity_id

    async def test_dump__without_constraint(self) -> None:
        sut = EntityReference()
        entity_type = DummyEntityOne.plugin
        entity_id = "123"
        sut.entity_type = entity_type.id
        sut.entity_id = entity_id
        expected = {
            "entity_type": entity_type.id,
            "entity": entity_id,
        }
        assert sut.dump() == expected

    async def test_validate__without_constraint_without_importable_entity_type_should_error(
        self,
    ) -> None:
        sut = EntityReference("betty.non_existent.Entity")
        with raises_error(error_type=HumanFacingException):
            await sut.validate(StaticPluginRepository(EntityDefinition))


class TestEntityReferenceSequence(ConfigurationSequenceTestBase[EntityReference]):
    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[EntityReference, int]:
        return EntityReferenceSequence

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[EntityReference]:
        return (
            EntityReference(),
            EntityReference(DummyEntityOne.plugin),
            EntityReference(DummyEntityOne.plugin, "123"),
            EntityReference(
                DummyEntityOne.plugin,
                "123",
                entity_type_is_constrained=True,
            ),
        )

    async def test__pre_add__with_missing_required_entity_type(self) -> None:
        sut = EntityReferenceSequence(entity_type_constraint=DummyEntityOne.plugin)
        with pytest.raises(HumanFacingException):
            sut.append(EntityReference())

    async def test__pre_add__with_invalid_required_entity_type(self) -> None:
        sut = EntityReferenceSequence(entity_type_constraint=DummyEntityOne.plugin)
        with pytest.raises(HumanFacingException):
            sut.append(EntityReference(DummyEntityTwo.plugin))

    async def test__pre_add__with_valid_value(self) -> None:
        sut = EntityReferenceSequence(entity_type_constraint=DummyEntityOne.plugin)
        sut.append(EntityReference(DummyEntityOne.plugin))

    async def test_validate__with_invalid_item(
        self,
    ) -> None:
        sut = EntityReferenceSequence([EntityReference("betty.non_existent.Entity")])
        with raises_error(error_type=HumanFacingException):
            await sut.validate(StaticPluginRepository(EntityDefinition))
