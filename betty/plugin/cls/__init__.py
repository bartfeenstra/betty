"""
Classed plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, final, override

from betty.definition.cls import ClassedDefinition
from betty.importlib import fully_qualified_name
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class Plugin[PluginDefinitionT: ClassedPluginDefinition]:
    """
    A plugin class.

    Classed plugins may optionally subclass this class to expose their plugin definitions.
    """

    @final
    @classmethod
    def plugin(cls) -> PluginDefinitionT:
        """
        The plugin definition.
        """
        try:
            return _plugins[cls]  # ty:ignore[invalid-return-type]
        except KeyError:  # pragma: no cover
            raise NotImplementedError(
                f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(ClassedPluginDefinition)} subclass."
            ) from None


class ClassedPluginDefinition[PluginT = Any](
    ClassedDefinition[PluginT], PluginDefinition
):
    """
    A classed plugin definition.
    """

    @override
    def _set_cls(self, cls: type[PluginT], /) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Plugin):
            _plugins[cls] = self


_plugins: Final[MutableMapping[type, ClassedPluginDefinition[Any]]] = {}
