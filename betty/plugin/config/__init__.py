"""
Configurable plugins.
"""

from __future__ import annotations

from typing import Any, final

from betty.data import Data
from betty.definition import ResolvableDefinition, resolve_definition
from betty.definition.id import ResolvableId, resolve_id
from betty.exception import HumanFacingException
from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.config.factory import ConfigurablePlugin


class ConfigurablePluginDefinition[PluginT, ConfigT: Data](
    ClassedPluginDefinition[ConfigurablePlugin[PluginT, ConfigT]]
):
    """
    A configurable plugin definition.
    """

    def __init__(
        self,
        *args: Any,
        config_cls: type[ConfigT] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.__config_cls = config_cls

    @property
    def config_cls(self) -> type[ConfigT]:
        """
        The plugin's configuration class, if it is configurable.
        """
        if not self.__config_cls:
            # @todo Add args
            raise NotConfigurable
        return self.__config_cls


@final
class NotConfigurable(HumanFacingException):
    """
    Raised when a plugin is not configurable.
    """

    def __init__[DefinitionT: PluginDefinition](
        self,
        plugin_type: ResolvableDefinition[PluginTypeDefinition[DefinitionT]],
        plugin_id: ResolvableId[DefinitionT],
        /,
    ):
        super().__init__(
            _("{plugin_type} {plugin} is not configurable").format(
                plugin_type=resolve_definition(plugin_type).label,
                plugin=Quote(resolve_id(plugin_id)),
            )
        )
