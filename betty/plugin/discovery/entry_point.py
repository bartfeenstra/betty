"""
Discover plugins defined as distribution package entry points.
"""

from __future__ import annotations

from importlib import metadata
from typing import TYPE_CHECKING, Generic, final

from typing_extensions import TypeVar, override

from betty.plugin import PluginDefinition, resolve_definition
from betty.plugin.discovery import PluginDiscovery

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.service_level import ServiceLevel

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class EntryPointDiscovery(
    PluginDiscovery[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
    """
    Discover plugins defined as distribution package `entry points <https://packaging.python.org/en/latest/specifications/entry-points/>`_.

    If you are developing a plugin for an existing plugin type that uses entry points, you'll have
    to add that plugin to your package metadata. For example, for a plugin type

    - whose entry point group is ``your_entry_point_group``
    - with a plugin class ``MyPlugin`` in the module ``my_package.my_module``
    - and a plugin ID ``my-package-plugin``:

    .. code-block:: toml

        [project.entry-points.'betty.your_entry_point_group']
        'my-package-plugin' = 'my_package.my_module:MyPlugin'
    """

    def __init__(
        self,
        entry_point_group: str,
        /,
    ):
        self._entry_point_group = entry_point_group

    @override
    async def discover(
        self, service_level: ServiceLevel, /
    ) -> Iterable[_PluginDefinitionT]:
        return [
            resolve_definition(entry_point.load())  # type: ignore[misc]
            for entry_point in metadata.entry_points(group=self._entry_point_group)
        ]
