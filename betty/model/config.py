"""
Configuration for the data model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, final

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_none,
    assert_or,
    assert_record,
    assert_setattr,
    assert_str,
)
from betty.assertion.error import AssertionFailed
from betty.config import Configuration
from betty.config.collections.sequence import ConfigurationSequence
from betty.locale.localizable import _
from betty.machine_name import MachineName, assert_machine_name
from betty.model import Entity
from betty.plugin import PluginIdentifier, PluginRepository, resolve_identifier
from betty.plugin.assertion import assert_plugin

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.serde.dump import Dump, DumpMapping


_EntityCoT = TypeVar("_EntityCoT", bound=Entity, covariant=True)


@final
class EntityReference(Configuration, Generic[_EntityCoT]):
    """
    Configuration that references an entity from the project's ancestry.
    """

    def __init__(
        self,
        entity_type: PluginIdentifier[_EntityCoT] | None = None,
        entity_id: str | None = None,
        *,
        entity_type_is_constrained: bool = False,
    ):
        super().__init__()
        self._entity_type = (
            None if entity_type is None else resolve_identifier(entity_type)
        )
        self._entity_id = entity_id
        self._entity_type_is_constrained = entity_type_is_constrained

    @property
    def entity_type(self) -> MachineName | None:
        """
        The referenced entity's type.
        """
        return self._entity_type

    @entity_type.setter
    def entity_type(self, entity_type: PluginIdentifier[_EntityCoT]) -> None:
        if self._entity_type_is_constrained:
            raise AttributeError(
                f"The entity type cannot be set, as it is already constrained to {self._entity_type}."
            )
        self._entity_type = resolve_identifier(entity_type)

    @property
    def entity_id(self) -> str | None:
        """
        The referenced entity's ID.
        """
        return self._entity_id

    @entity_id.setter
    def entity_id(self, entity_id: str) -> None:
        self._entity_id = entity_id

    @entity_id.deleter
    def entity_id(self) -> None:
        self._entity_id = None

    @property
    def entity_type_is_constrained(self) -> bool:
        """
        Whether the entity type may be changed.
        """
        return self._entity_type_is_constrained

    @override
    def load(self, dump: Dump) -> None:
        if isinstance(dump, dict) or not self.entity_type_is_constrained:
            assert_record(
                RequiredField(
                    "entity_type",
                    assert_or(
                        assert_none(),
                        assert_machine_name() | assert_setattr(self, "_entity_type"),
                    ),
                ),
                OptionalField(
                    "entity",
                    assert_str() | assert_setattr(self, "entity_id"),
                ),
            )(dump)
        else:
            assert_str()(dump)
            assert_setattr(self, "entity_id")(dump)

    @override
    def dump(self) -> DumpMapping[Dump] | str | None:
        if self.entity_type_is_constrained:
            return self.entity_id

        dump: DumpMapping[Dump] = {"entity_type": self.entity_type}
        if self.entity_id is not None:
            dump["entity"] = self.entity_id
        return dump

    async def validate(self, entity_type_repository: PluginRepository[Entity]) -> None:
        """
        Validate the configuration.
        """
        assert_plugin(await entity_type_repository.mapping())(self.entity_type)


@final
class EntityReferenceSequence(
    Generic[_EntityCoT], ConfigurationSequence[EntityReference[_EntityCoT]]
):
    """
    Configuration for a sequence of references to entities from the project's ancestry.
    """

    def __init__(
        self,
        entity_references: Iterable[EntityReference[_EntityCoT]] | None = None,
        *,
        entity_type_constraint: PluginIdentifier[_EntityCoT] | None = None,
    ):
        self._entity_type_constraint = (
            None
            if entity_type_constraint is None
            else resolve_identifier(entity_type_constraint)
        )
        super().__init__(entity_references)

    @override
    def _load_item(self, dump: Dump) -> EntityReference[_EntityCoT]:
        configuration = EntityReference[_EntityCoT](
            # Use a dummy entity type for now to satisfy the initializer.
            # It will be overridden when loading the dump.
            Entity  # type: ignore[arg-type]
            if self._entity_type_constraint is None
            else self._entity_type_constraint,
            entity_type_is_constrained=self._entity_type_constraint is not None,
        )
        configuration.load(dump)
        return configuration

    @override
    def _pre_add(self, configuration: EntityReference[_EntityCoT]) -> None:
        super()._pre_add(configuration)

        entity_type_constraint = self._entity_type_constraint
        entity_reference_entity_type = configuration._entity_type

        if entity_type_constraint is None:
            configuration._entity_type_is_constrained = False
            return

        configuration._entity_type_is_constrained = True

        if (
            entity_reference_entity_type == entity_type_constraint
            and configuration.entity_type_is_constrained
        ):
            return

        if entity_reference_entity_type is None:
            raise AssertionFailed(
                _(
                    "The entity reference must be for an entity of type {expected_entity_type_id}, but instead does not specify an entity type at all."
                ).format(
                    expected_entity_type_id=entity_type_constraint,
                )
            )

        raise AssertionFailed(
            _(
                "The entity reference must be for an entity of type {expected_entity_type_id}, but instead is for an entity of type {actual_entity_type_id}."
            ).format(
                expected_entity_type_id=entity_type_constraint,
                actual_entity_type_id=entity_reference_entity_type,
            )
        )

    async def validate(self, entity_type_repository: PluginRepository[Entity]) -> None:
        """
        Validate the configuration.
        """
        for reference in self:
            await reference.validate(entity_type_repository)
