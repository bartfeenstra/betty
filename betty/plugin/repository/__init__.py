"""
Access discovered plugins.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic

from typing_extensions import TypeVar

from betty.config import Configurable, Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.json.schema import Enum
from betty.locale.localizable.gettext import _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import Plugin, PluginDefinition
from betty.string import kebab_case_to_lower_camel_case
from betty.typing import Void, Voidable

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.plugin.resolve import ResolvableId
    from betty.serde.dump import Dump
    from betty.service.level.factory import AnyFactory

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginRepository(ABC, Generic[_PluginDefinitionT, _PluginT]):
    """
    Access discovered plugins.
    """

    def __init__(self, plugin_type: type[_PluginDefinitionT], *, factory: AnyFactory):
        self._type = plugin_type
        self._factory = factory
        self._plugin_id_schema: Enum | None = None

    @property
    def type(self) -> type[_PluginDefinitionT]:
        """
        The plugin type contained by this repository.
        """
        return self._type

    @abstractmethod
    def get(
        self, plugin_id: ResolvableId[_PluginDefinitionT, _PluginT], /
    ) -> _PluginDefinitionT:
        """
        Get a single plugin by its ID.

        :raises PluginUnavailable: if no plugin can be found for the given ID.
        """

    def __len__(self) -> int:
        return len(list(self.__iter__()))

    @abstractmethod
    def __iter__(self) -> Iterator[_PluginDefinitionT]:
        pass

    def __getitem__(
        self, plugin_id: ResolvableId[_PluginDefinitionT, _PluginT]
    ) -> _PluginDefinitionT:
        return self.get(plugin_id)

    @property
    def plugin_id_schema(self) -> Enum:
        """
        Get the JSON schema for the IDs of the plugins in this repository.
        """
        if self._plugin_id_schema is None:
            label = self._type.type.label.localize(DEFAULT_LOCALIZER)
            self._plugin_id_schema = Enum(
                *[plugin.id for plugin in self],  # noqa A002
                def_name=kebab_case_to_lower_camel_case(self._type.type.id),
                title=label,
                description=f"A {label} plugin ID",
            )
        return self._plugin_id_schema

    async def new_target(
        self,
        target: ResolvableId[_PluginDefinitionT, _PluginT],
        configuration: Voidable[Configuration | Dump] = Void(),  # noqa B008
    ) -> _PluginT:
        """
        Create a new plugin instance.

        :raises FactoryError: raised when ``target`` could not be called.
        """
        plugin_definition = self[target]
        if not isinstance(configuration, Void):
            if not issubclass(plugin_definition.cls, Configurable):
                raise HumanFacingException(
                    _(
                        'Plugin "{plugin_id}" is not configurable, but configuration was given.'
                    ).format(plugin_id=plugin_definition.id)
                )
            if not issubclass(plugin_definition.cls, ConfigurationDependentSelfFactory):
                raise HumanFacingException(
                    f"Cannot instantiate {fully_qualified_name(plugin_definition.cls)} with configuration because it does not subclass {fully_qualified_name(ConfigurationDependentSelfFactory)}."
                )
            if isinstance(configuration, Configuration):
                configuration = configuration
            else:
                configuration = plugin_definition.cls.configuration_cls().load(
                    configuration
                )
            return await self._factory(
                plugin_definition.cls.new_for_configuration(configuration)  # type: ignore[arg-type]
            )
        return await self._factory(
            plugin_definition.cls,  # type: ignore[arg-type]
        )
