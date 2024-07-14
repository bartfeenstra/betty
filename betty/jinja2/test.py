"""
Provide Betty's default Jinja2 tests.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from betty.json.linked_data import LinkedDataDumpable
from betty.locale.date import DateRange
from betty.model import (
    Entity,
    GeneratedEntityId,
    UserFacingEntity,
    ENTITY_TYPE_REPOSITORY,
)
from betty.model.ancestry import (
    HasLinks,
    HasFileReferences,
    is_private,
    is_public,
    Event,
)
from betty.model.presence_role import Subject, Witness
from betty.model.event_type import StartOfLifeEventType, EndOfLifeEventType

if TYPE_CHECKING:
    from betty.plugin import PluginId


def test_linked_data_dumpable(value: Any) -> bool:
    """
    Test if a value can be dumped to Linked Data.
    """
    return isinstance(value, LinkedDataDumpable)


async def test_entity(value: Any, entity_type_id: PluginId | None = None) -> bool:
    """
    Test if a value is an entity.

    :param entity_type_id: If given, additionally ensure the value is an entity of this type.
    """
    cls = await ENTITY_TYPE_REPOSITORY.get(entity_type_id) if entity_type_id else Entity
    return isinstance(value, cls)


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
    Test if a value has :py:class:`betty.model.ancestry.FileReference` entities associated with it.
    """
    return isinstance(value, HasFileReferences)


def test_has_generated_entity_id(value: Any) -> bool:
    """
    Test if a value is a generated entity ID, or if it is an entity and has a generated entity ID.
    """
    if isinstance(value, GeneratedEntityId):
        return True
    if isinstance(value, Entity):
        return isinstance(value.id, GeneratedEntityId)
    return False


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
    return issubclass(event.event_type, StartOfLifeEventType)


def test_end_of_life_event(event: Event) -> bool:
    """
    Test if an event is an end-of-life event.
    """
    return issubclass(event.event_type, EndOfLifeEventType)


TESTS = {
    "date_range": test_date_range,
    "end_of_life_event": test_end_of_life_event,
    "entity": test_entity,
    "has_file_references": test_has_file_references,
    "has_generated_entity_id": test_has_generated_entity_id,
    "has_links": test_has_links,
    "linked_data_dumpable": test_linked_data_dumpable,
    "private": is_private,
    "public": is_public,
    "start_of_life_event": test_start_of_life_event,
    "subject_role": test_subject_role,
    "user_facing_entity": test_user_facing_entity,
    "witness_role": test_witness_role,
}
