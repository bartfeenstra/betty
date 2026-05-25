"""
Classed plugins.
"""

from __future__ import annotations

from typing import Any, TypeVar, final, override

from betty.definition.cls import ClsDefinition
from betty.importlib import fully_qualified_name
from betty.plugin import PluginDefinition

_PLUGINS = {}


class Plugin[PluginClsDefinitionT: PluginClsDefinition]:
    """
    A plugin class.

    Classed plugins may optionally subclass this class to expose their plugin definitions.
    """

    @final
    @classmethod
    def plugin(cls) -> PluginClsDefinitionT:
        """
        The plugin definition.
        """
        try:
            return _PLUGINS[cls]
        except KeyError:
            raise NotImplementedError(
                f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginClsDefinition)} subclass."
            ) from None


_PluginClsDefinitionPluginT = TypeVar(
    "_PluginClsDefinitionPluginT", covariant=True, default=Any
)


class PluginClsDefinition(PluginDefinition, ClsDefinition[_PluginClsDefinitionPluginT]):
    """
    A classed plugin definition.
    """

    @override
    def _set_cls(self, cls: type[_PluginClsDefinitionPluginT], /) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Plugin):
            _PLUGINS[cls] = self
