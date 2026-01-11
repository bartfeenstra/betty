"""
Configuration for the data model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.assertion import (
    RequiredField,
    assert_record,
    assert_str,
)
from betty.config import Configuration, Sample
from betty.config.collections.sequence import ConfigurationSequence
from betty.data.indicator.selector import Index
from betty.exception import HumanFacingExceptionGroup
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin.assertion import assert_plugin
from betty.plugin.resolve import ResolvableId, resolve_id

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.model import EntityDefinition
    from betty.plugin.repository import PluginRepository
    from betty.serde.dump import Dump, DumpMapping


@final
class EntityReference(Configuration):
    """
    Configuration that references an entity from the project's ancestry.

    .. configuration:: betty.model.config:EntityReference
    """

    def __init__(self, entity_type: ResolvableId[EntityDefinition], entity_id: str, /):
        super().__init__()
        self.entity_type = entity_type  # type: ignore[assignment]
        self.entity_id = entity_id

    @property
    def entity_type(self) -> MachineName:
        """
        The referenced entity's type.
        """
        return self._entity_type

    @entity_type.setter
    def entity_type(self, entity_type: ResolvableId[EntityDefinition]) -> None:
        self._entity_type = resolve_id(entity_type)

    @property
    def entity_id(self) -> str:
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

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.entity_type, self.entity_id) == (
            other.entity_type,
            other.entity_id,
        )

    async def validate(
        self, entity_type_repository: PluginRepository[EntityDefinition], /
    ) -> None:
        """
        Validate the configuration.
        """
        assert_plugin(entity_type_repository)(self.entity_type)

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.ancestry.person import Person

        yield Sample(cls(Person, "123"), label="Default")


@final
class EntityReferenceSequence(ConfigurationSequence[EntityReference]):
    """
    Configuration for a sequence of references to entities from the project's ancestry.

    .. configuration:: betty.model.config:EntityReferenceSequence
    """

    @override
    @classmethod
    def _item_cls(cls) -> type[EntityReference]:
        return EntityReference

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

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.ancestry.person import Person

        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(cls([EntityReference(Person, "123")]), label="Expanded", full=True)
