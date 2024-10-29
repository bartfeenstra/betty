"""
Provide Betty's default Jinja2 tests.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, Self

from typing_extensions import override

from betty.ancestry.event_type.event_types import (
    StartOfLifeEventType,
    EndOfLifeEventType,
)
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import HasLinks
from betty.ancestry.presence_role.presence_roles import Subject, Witness
from betty.date import DateRange
from betty.factory import IndependentFactory
from betty.json.linked_data import LinkedDataDumpable
from betty.model import (
    Entity,
    UserFacingEntity,
    ENTITY_TYPE_REPOSITORY,
    persistent_id,
)
from betty.privacy import is_private, is_public
from betty.typing import internal

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from collections.abc import Mapping, Callable
    from betty.ancestry.event import Event
    from betty.plugin import PluginIdToTypeMapping


def test_linked_data_dumpable(value: Any) -> bool:
    """
    Test if a value can be dumped to Linked Data.
    """
    return isinstance(value, LinkedDataDumpable)


class TestEntity(IndependentFactory):
    """
    Test if a value is an entity.
    """

    def __init__(self, entity_type_id_to_type_mapping: PluginIdToTypeMapping[Entity]):
        self._entity_type_id_to_type_mapping = entity_type_id_to_type_mapping

    @override
    @classmethod
    async def new(cls) -> Self:
        return cls(await ENTITY_TYPE_REPOSITORY.mapping())

    def __call__(
        self, value: Any, entity_type_identifier: MachineName | None = None
    ) -> bool:
        """
        :param entity_type_id: If given, additionally ensure the value is an entity of this type.
        """
        if entity_type_identifier is not None:
            entity_type = self._entity_type_id_to_type_mapping[entity_type_identifier]
        else:
            entity_type = Entity  # type: ignore[type-abstract]
        return isinstance(value, entity_type)


def test_user_facing_entity(value: Any) -> bool:
    """
    Test if a value is an entity of a user-facing type.
    """
    return isinstance(value, UserFacingEntity)


def test_has_links(value: Any) -> bool:
    """
    Test if a value has external links associated with it.
    """
    return isinstance(value, HasLinks)


def test_has_file_references(value: Any) -> bool:
    """
    Test if a value has :py:class:`betty.ancestry.file_reference.FileReference` entities associated with it.
    """
    return isinstance(value, HasFileReferences)


def test_subject_role(value: Any) -> bool:
    """
    Test if a presence role is that of Subject.
    """
    return isinstance(value, Subject)


def test_witness_role(value: Any) -> bool:
    """
    Test if a presence role is that of Witness.
    """
    return isinstance(value, Witness)


def test_date_range(value: Any) -> bool:
    """
    Test if a value is a date range.
    """
    return isinstance(value, DateRange)


def test_start_of_life_event(event: Event) -> bool:
    """
    Test if an event is a start-of-life event.
    """
    return isinstance(event.event_type, StartOfLifeEventType)


def test_end_of_life_event(event: Event) -> bool:
    """
    Test if an event is an end-of-life event.
    """
    return isinstance(event.event_type, EndOfLifeEventType)


@internal
async def tests() -> Mapping[str, Callable[..., bool]]:
    """
    Define the available tests.
    """
    return {
        "date_range": test_date_range,
        "end_of_life_event": test_end_of_life_event,
        "entity": await TestEntity.new(),
        "has_file_references": test_has_file_references,
        "persistent_entity_id": persistent_id,
        "has_links": test_has_links,
        "linked_data_dumpable": test_linked_data_dumpable,
        "private": is_private,
        "public": is_public,
        "start_of_life_event": test_start_of_life_event,
        "subject_role": test_subject_role,
        "user_facing_entity": test_user_facing_entity,
        "witness_role": test_witness_role,
    }
