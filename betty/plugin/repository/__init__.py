"""
Access discovered plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVar

from betty.json.schema import Enum
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import PluginDefinition
from betty.string import kebab_case_to_lower_camel_case

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.machine_name import MachineName

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginRepository(ABC, Generic[_PluginDefinitionT]):
    """
    Access discovered plugins.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],
    ):
        self._type = plugin_type
        self._plugin_id_schema: Enum | None = None

    @property
    def type(self) -> type[_PluginDefinitionT]:
        """
        The plugin type contained by this repository.
        """
        return self._type

    @abstractmethod
    def get(self, plugin_id: MachineName, /) -> _PluginDefinitionT:
        """
        Get a single plugin by its ID.

        :raises PluginUnavailable: if no plugin can be found for the given ID.
        """

    def __len__(self) -> int:
        return len(list(self.__iter__()))

    @abstractmethod
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        pass

    def __getitem__(self, plugin_id: MachineName) -> _PluginDefinitionT:
        return self.get(plugin_id)

    @property
    def plugin_id_schema(self) -> Enum:
        """
        Get the JSON schema for the IDs of the plugins in this repository.
        """
        if self._plugin_id_schema is None:
            label = self._type.type().label.localize(DEFAULT_LOCALIZER)
            self._plugin_id_schema = Enum(
                *[plugin.id for plugin in self],  # noqa A002
                def_name=kebab_case_to_lower_camel_case(self._type.type().id),
                title=label,
                description=f"A {label} plugin ID",
            )
        return self._plugin_id_schema
