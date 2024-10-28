from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

import pytest

from betty.assertion.error import AssertionFailed
from betty.model import Entity
from betty.model.config import EntityReference, EntityReferenceSequence
from betty.plugin.static import StaticPluginRepository
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from betty.serde.dump import Dump


class EntityReferenceTestEntityOne(DummyEntity):
    pass


class EntityReferenceTestEntityTwo(DummyEntity):
    pass


class EntityReferenceSequenceTestEntity(DummyEntity):
    pass


class TestEntityReference:
    async def test_entity_type_with_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne](
            entity_type, None, entity_type_is_constrained=True
        )
        assert sut.entity_type == entity_type.plugin_id()
        with pytest.raises(AttributeError):
            sut.entity_type = entity_type.plugin_id()

    async def test_entity_type_without_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne]()
        assert sut.entity_type is None
        sut.entity_type = entity_type.plugin_id()
        assert sut.entity_type == entity_type.plugin_id()

    async def test_entity_type_is_constrained(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne](
            entity_type, None, entity_type_is_constrained=True
        )
        assert sut.entity_type_is_constrained

    async def test_entity_id(self) -> None:
        entity_id = "123"
        sut = EntityReference[EntityReferenceTestEntityOne]()
        assert sut.entity_id is None
        sut.entity_id = entity_id
        assert sut.entity_id == entity_id
        del sut.entity_id
        assert sut.entity_id is None

    async def test_load_with_constraint(self) -> None:
        sut = EntityReference(
            EntityReferenceTestEntityOne, entity_type_is_constrained=True
        )
        entity_id = "123"
        dump = entity_id
        sut.load(dump)
        assert sut.entity_id == entity_id

    @pytest.mark.parametrize(
        "dump",
        [
            {
                "entity_type": EntityReferenceTestEntityOne,
                "entity": "123",
            },
            {
                "entity_type": EntityReferenceTestEntityTwo,
                "entity": "123",
            },
            False,
            123,
        ],
    )
    async def test_load_with_constraint_without_string_should_error(
        self, dump: Dump
    ) -> None:
        sut = EntityReference(
            EntityReferenceTestEntityOne, entity_type_is_constrained=True
        )
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityReferenceTestEntityOne),
        )
        entity_type = EntityReferenceTestEntityOne
        entity_id = "123"
        dump: Dump = {
            "entity_type": entity_type.plugin_id(),
            "entity": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        sut.load(dump)
        assert sut.entity_type == entity_type.plugin_id()
        assert sut.entity_id == entity_id

    async def test_load_without_constraint_without_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint_without_string_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity_type": 123,
            "entity": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint_without_string_entity_id_should_error(
        self,
    ) -> None:
        entity_type = EntityReferenceTestEntityOne
        dump: Dump = {
            "entity_type": entity_type.plugin_id(),
            "entity": None,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_with_constraint(self) -> None:
        sut = EntityReference[Entity](Entity, None, entity_type_is_constrained=True)
        entity_id = "123"
        sut.entity_id = entity_id
        assert sut.dump() == entity_id

    async def test_dump_without_constraint(self) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_type = EntityReferenceTestEntityOne
        entity_id = "123"
        sut.entity_type = entity_type.plugin_id()
        sut.entity_id = entity_id
        expected = {
            "entity_type": entity_type.plugin_id(),
            "entity": entity_id,
        }
        assert sut.dump() == expected

    async def test_validate_without_constraint_without_importable_entity_type_should_error(
        self,
    ) -> None:
        sut = EntityReference[Entity]("betty.non_existent.Entity")
        with raises_error(error_type=AssertionFailed):
            await sut.validate(StaticPluginRepository())


class TestEntityReferenceSequence(
    ConfigurationSequenceTestBase[EntityReference[Entity]]
):
    @pytest.fixture(autouse=True)
    def _entity_types(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityReferenceSequenceTestEntity),
        )

    async def get_sut(
        self, configurations: Iterable[EntityReference[Entity]] | None = None
    ) -> EntityReferenceSequence[Entity]:
        return EntityReferenceSequence(configurations)

    async def get_configurations(
        self,
    ) -> tuple[
        EntityReference[Entity],
        EntityReference[Entity],
        EntityReference[Entity],
        EntityReference[Entity],
    ]:
        return (
            EntityReference[Entity](),
            EntityReference[Entity](EntityReferenceSequenceTestEntity),
            EntityReference[Entity](EntityReferenceSequenceTestEntity, "123"),
            EntityReference[Entity](
                EntityReferenceSequenceTestEntity,
                "123",
                entity_type_is_constrained=True,
            ),
        )

    async def test_pre_add_with_missing_required_entity_type(self) -> None:
        class DummyConstraintedEntity(DummyEntity):
            pass

        sut = EntityReferenceSequence(entity_type_constraint=DummyConstraintedEntity)
        with pytest.raises(AssertionFailed):
            sut.append(
                EntityReference(DummyEntity)  # type: ignore[arg-type]
            )

    async def test_pre_add_with_invalid_required_entity_type(self) -> None:
        class DummyConstraintedEntity(DummyEntity):
            pass

        sut = EntityReferenceSequence(entity_type_constraint=DummyConstraintedEntity)
        with pytest.raises(AssertionFailed):
            sut.append(EntityReference())

    async def test_pre_add_with_valid_value(self) -> None:
        sut = EntityReferenceSequence(entity_type_constraint=DummyEntity)
        sut.append(EntityReference(DummyEntity))

    async def test_validate_with_invalid_item(
        self,
    ) -> None:
        sut = EntityReferenceSequence[Entity](
            [EntityReference("betty.non_existent.Entity")]
        )
        with raises_error(error_type=AssertionFailed):
            await sut.validate(StaticPluginRepository())
