"""
Configuration for the data model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.assertion import (
    RequiredField,
    assert_record,
    assert_str,
)
from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.data import Index
from betty.exception import HumanFacingExceptionGroup
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin.assertion import assert_plugin
from betty.plugin.resolve import ResolvableId, resolve_id

if TYPE_CHECKING:
    from betty.model import EntityDefinition
    from betty.plugin.repository import PluginRepository
    from betty.serde.dump import Dump, DumpMapping


@final
class EntityReference(Configuration):
    """
    Configuration that references an entity from the project's ancestry.
    """

    def __init__(self, entity_type: ResolvableId[EntityDefinition], entity_id: str, /):
        super().__init__()
        self.entity_type = entity_type  # type: ignore[assignment]
        self.entity_id = entity_id

    @property
    def entity_type(self) -> MachineName | None:
        """
        The referenced entity's type.
        """
        return self._entity_type

    @entity_type.setter
    def entity_type(self, entity_type: ResolvableId[EntityDefinition]) -> None:
        self._entity_type = resolve_id(entity_type)

    @property
    def entity_id(self) -> str | None:
        """
        The referenced entity's ID.
        """
        return self._entity_id

    @entity_id.setter
    def entity_id(self, entity_id: str) -> None:
        self._entity_id = entity_id

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        record = assert_record(
            RequiredField("type", assert_machine_name()),
            RequiredField("id", assert_str()),
        )(dump)
        return cls(record["type"], record["id"])

    @override
    def dump(self) -> DumpMapping[Dump] | str | None:
        return {
            "type": self.entity_type,
            "id": self.entity_id,
        }

    async def validate(
        self, entity_type_repository: PluginRepository[EntityDefinition], /
    ) -> None:
        """
        Validate the configuration.
        """
        assert_plugin(entity_type_repository)(self.entity_type)


@final
class EntityReferenceSequence(ConfigurationSequence[EntityReference]):
    """
    Configuration for a sequence of references to entities from the project's ancestry.
    """

    @override
    @classmethod
    def _load_item(cls, dump: Dump, /) -> EntityReference:
        return EntityReference.load(dump)

    async def validate(
        self, entity_type_repository: PluginRepository[EntityDefinition], /
    ) -> None:
        """
        Validate the configuration.
        """
        with HumanFacingExceptionGroup() as errors:
            for index, reference in enumerate(self):
                with errors.absorb(Index(index)):
                    await reference.validate(entity_type_repository)
