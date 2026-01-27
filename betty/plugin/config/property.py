"""
Plugin configuration attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from typing_extensions import TypeVar

from betty.collections import ResolvingMutableSequence
from betty.data.aggregate.record.object.property import Property
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.config import (
    PluginConfiguration,
    ResolvablePluginConfiguration,
    ResolvablePluginConfigurations,
    resolve_plugin_configuration,
    resolve_plugin_configurations,
)
from betty.plugin.data import PluginConfigurationSequenceDefinition

if TYPE_CHECKING:
    from betty.locale.localizable import LocalizableLike

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class PluginConfigurationSequenceProperty(
    Property[
        ResolvingMutableSequence[
            PluginConfiguration[_PluginDefinitionT, _PluginT],
            ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT],
        ],
        ResolvablePluginConfigurations[_PluginDefinitionT, _PluginT],
    ]
):
    """
    A property containing a :py:class:`betty.plugin.config.PluginConfiguration`.
    """

    def __init__(
        self,
        plugin_type: type[_PluginDefinitionT],
        *,
        label: LocalizableLike | None = None,
        description: LocalizableLike | None = None,
    ):
        super().__init__(
            PluginConfigurationSequenceDefinition(plugin_type),
            label=label,
            description=description,
            resolver=resolve_plugin_configurations,
            default=lambda: ResolvingMutableSequence([], resolve_plugin_configuration),
        )

    def __set__(
        self,
        instance: Any,
        value: ResolvingMutableSequence[
            PluginConfiguration[_PluginDefinitionT, _PluginT],
            ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT],
        ]
        | ResolvablePluginConfigurations[_PluginDefinitionT, _PluginT],
    ) -> None:
        configurations = self.__get__(instance, type(instance))
        configurations.clear()
        configurations.extend(self._resolver(value))
