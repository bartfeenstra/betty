"""
Provide Betty's default Jinja2 tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from betty.ancestry.event_type import EventTypeDefinition
from betty.ancestry.gender import GenderDefinition
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_links import HasLinks
from betty.ancestry.place_type import PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.copyright_notice import CopyrightNoticeDefinition
from betty.date import DateRange
from betty.image import is_supported_media_type
from betty.json.linked_data import LinkedDataDumpable
from betty.license import LicenseDefinition
from betty.model import EntityDefinition, persistent_id
from betty.plugin import ClassedPluginTypeDefinition, PluginDefinition
from betty.privacy import is_private, is_public
from betty.string import kebab_case_to_snake_case
from betty.typing import internal
from betty.user import UserFacing

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from betty.machine_name import MachineName
    from betty.media_type import MediaType

_PluginDefinitionCoT = TypeVar("_PluginDefinitionCoT", bound=PluginDefinition)


def test_linked_data_dumpable(value: Any) -> bool:
    """
    Test if a value can be dumped to Linked Data.
    """
    return isinstance(value, LinkedDataDumpable)


class PluginTester:
    """
    Provides tests for a specific plugin type.
    """

    def __init__(self, plugin_type: ClassedPluginTypeDefinition):
        self._plugin_type = plugin_type

    def tests(self) -> Mapping[str, Callable[..., bool]]:
        """
        Get the available tests, keyed by test name.
        """
        return {f"{kebab_case_to_snake_case(self._plugin_type.id)}_plugin": self}

    def __call__(self, value: Any, plugin_id: MachineName | None = None) -> bool:
        """
        :param entity_type_id: If given, additionally ensure the value is an instance of this type.
        """
        assert self._plugin_type.cls is not None
        if not isinstance(value, self._plugin_type.cls):
            return False
        if plugin_id is not None and value.plugin.id != plugin_id:  # type: ignore[attr-defined]
            return False
        return True


def test_user_facing(value: Any) -> bool:
    """
    Test if a value is of a user-facing type.
    """
    return (
        isinstance(value, UserFacing)
        or isinstance(value, type)
        and issubclass(value, UserFacing)
    )


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


def test_date_range(value: Any) -> bool:
    """
    Test if a value is a date range.
    """
    return isinstance(value, DateRange)


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
        "has_file_references": test_has_file_references,
        "persistent_entity_id": persistent_id,
        "has_links": test_has_links,
        "image_supported_media_type": test_image_supported_media_type,
        "linked_data_dumpable": test_linked_data_dumpable,
        "private": is_private,
        "public": is_public,
        "user_facing": test_user_facing,
        **(PluginTester(CopyrightNoticeDefinition.type)).tests(),
        **(PluginTester(EntityDefinition.type)).tests(),
        **(PluginTester(EventTypeDefinition.type)).tests(),
        **(PluginTester(GenderDefinition.type)).tests(),
        **(PluginTester(LicenseDefinition.type)).tests(),
        **(PluginTester(PlaceTypeDefinition.type)).tests(),
        **(PluginTester(PresenceRoleDefinition.type)).tests(),
    }
