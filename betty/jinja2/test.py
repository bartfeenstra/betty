"""
Provide Betty's default Jinja2 tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar

from typing_extensions import override

from betty.ancestry.event_type import EventType
from betty.ancestry.event_type.event_types import (
    EndOfLifeEventType,
    StartOfLifeEventType,
)
from betty.ancestry.gender import Gender
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import HasLinks
from betty.ancestry.place_type import PlaceType
from betty.ancestry.presence_role import PresenceRole
from betty.ancestry.presence_role.presence_roles import Subject, Witness
from betty.copyright_notice import CopyrightNotice
from betty.date import DateRange
from betty.factory import IndependentFactory
from betty.image import is_supported_media_type
from betty.json.linked_data import LinkedDataDumpable
from betty.license import License
from betty.model import (
    ENTITY_TYPE_REPOSITORY,
    Entity,
    persistent_id,
)
from betty.plugin import Plugin
from betty.privacy import is_private, is_public
from betty.typing import internal
from betty.user import UserFacing
from betty.warnings import deprecated

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from betty.ancestry.event import Event
    from betty.machine_name import MachineName
    from betty.media_type import MediaType
    from betty.plugin import PluginIdToTypeMapping

_PluginT = TypeVar("_PluginT", bound=Plugin)


def test_linked_data_dumpable(value: Any) -> bool:
    """
    Test if a value can be dumped to Linked Data.
    """
    return isinstance(value, LinkedDataDumpable)


class PluginTester(Generic[_PluginT]):
    """
    Provides tests for a specific plugin type.
    """

    def __init__(self, plugin_type: type[_PluginT], plugin_type_name: str):
        self._plugin_type = plugin_type
        self._plugin_type_name = plugin_type_name

    def tests(self) -> Mapping[str, Callable[..., bool]]:
        """
        Get the available tests, keyed by test name.
        """
        return {f"{self._plugin_type_name}_plugin": self}

    def __call__(
        self, value: Any, plugin_identifier: MachineName | None = None
    ) -> bool:
        """
        :param entity_type_id: If given, additionally ensure the value is an entity of this type.
        """
        if not isinstance(value, self._plugin_type):
            return False
        if plugin_identifier is not None and value.plugin_id() != plugin_identifier:
            return False
        return True


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

    @deprecated(
        "This test has been deprecated since Betty 0.4.5, and will be removed in Betty 0.5. Instead use the `entity_plugin` test."
    )
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
    return isinstance(value, UserFacing)


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


@deprecated(
    "This test has been deprecated since Betty 0.4.5, and will be removed in Betty 0.5. Instead use the `presence_role_plugin` test."
)
def test_subject_role(value: Any) -> bool:
    """
    Test if a presence role is that of Subject.
    """
    return isinstance(value, Subject)


@deprecated(
    "This test has been deprecated since Betty 0.4.5, and will be removed in Betty 0.5. Instead use the `presence_role_plugin` test."
)
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


def test_image_supported_media_type(media_type: MediaType | None) -> bool:
    """
    Test if a media type is supported by the image API.
    """
    if media_type is None:
        return False
    return is_supported_media_type(media_type)


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
        "image_supported_media_type": test_image_supported_media_type,
        "linked_data_dumpable": test_linked_data_dumpable,
        "private": is_private,
        "public": is_public,
        "start_of_life_event": test_start_of_life_event,
        "subject_role": test_subject_role,
        "user_facing_entity": test_user_facing_entity,
        "witness_role": test_witness_role,
        **(
            PluginTester(
                CopyrightNotice,  # type: ignore[type-abstract]
                "copyright_notice",
            )
        ).tests(),
        **(
            PluginTester(
                Entity,  # type: ignore[type-abstract]
                "entity",
            )
        ).tests(),
        **(
            PluginTester(
                EventType,  # type: ignore[type-abstract]
                "event_type",
            )
        ).tests(),
        **(
            PluginTester(
                Gender,  # type: ignore[type-abstract]
                "gender",
            )
        ).tests(),
        **(
            PluginTester(
                License,  # type: ignore[type-abstract]
                "license",
            )
        ).tests(),
        **(
            PluginTester(
                PlaceType,  # type: ignore[type-abstract]
                "place_type",
            )
        ).tests(),
        **(
            PluginTester(
                PresenceRole,  # type: ignore[type-abstract]
                "presence_role",
            )
        ).tests(),
    }
