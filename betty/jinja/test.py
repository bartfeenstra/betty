"""
Provide Betty's default Jinja2 tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.ancestry.has_file_references import HasFileReferences
from betty.image import is_supported_media_type
from betty.json.linked_data import LinkedDataDumpableWithSchema
from betty.model import persistent_id
from betty.plugin import Plugin, PluginDefinition
from betty.privacy import is_public
from betty.service.level.universe import UNIVERSE
from betty.string import kebab_case_to_snake_case

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, MutableMapping

    from betty.machine_name import MachineName
    from betty.media_type import MediaType


def test_linked_data_dumpable(value: Any) -> bool:
    """
    Test if a value can be dumped to Linked Data.
    """
    return isinstance(value, LinkedDataDumpableWithSchema)


class PluginTester:
    """
    Provides tests for a specific plugin type.
    """

    def __init__(self, plugin_type: type[PluginDefinition], /):
        self._plugin_type = plugin_type

    def tests(self) -> Mapping[str, Callable[..., bool]]:
        """
        Get the available tests, keyed by test name.
        """
        return {f"{kebab_case_to_snake_case(self._plugin_type.type().id)}_plugin": self}

    def __call__(self, /, value: Any, plugin_id: MachineName | None = None) -> bool:
        """
        :param plugin_id: If given, additionally ensure the value is an instance of this type.
        """
        if not isinstance(value, Plugin):
            return False
        if not isinstance(value.plugin(), self._plugin_type):
            return False
        return not (plugin_id is not None and value.plugin().id != plugin_id)


def test_has_file_references(value: Any) -> bool:
    """
    Test if a value has :py:class:`betty.ancestry.file_reference.FileReference` entities associated with it.
    """
    return isinstance(value, HasFileReferences)


def test_image_supported_media_type(media_type: MediaType | None) -> bool:
    """
    Test if a media type is supported by the image API.
    """
    if media_type is None:
        return False
    return is_supported_media_type(media_type)


async def tests() -> Mapping[str, Callable[..., bool]]:
    """
    Define the available tests.
    """
    tests: MutableMapping[str, Callable[..., bool]] = {
        "has_file_references": test_has_file_references,
        "persistent_entity_id": persistent_id,
        "image_supported_media_type": test_image_supported_media_type,
        "linked_data_dumpable": test_linked_data_dumpable,
        "public": is_public,
    }
    for plugin in UNIVERSE.plugins:
        tests.update(PluginTester(plugin.type).tests())
    return tests
