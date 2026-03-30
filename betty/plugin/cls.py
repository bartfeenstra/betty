"""
Classed plugins.
"""

from __future__ import annotations

from functools import update_wrapper
from typing import TypeVar, override

from betty.definition.cls import ClsDefinition
from betty.importlib import fully_qualified_name
from betty.plugin import PluginDefinition


class Plugin[PluginClsDefinitionT: PluginClsDefinition]:
    """
    A plugin class.
    """

    @classmethod
    def plugin(cls) -> PluginClsDefinitionT:
        """
        The plugin definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginClsDefinition)} subclass."
        )


_PluginCoT = TypeVar("_PluginCoT", default=Plugin, covariant=True)


class PluginClsDefinition(PluginDefinition, ClsDefinition[_PluginCoT]):
    """
    A classed plugin definition.
    """

    @override
    def _set_cls(self, cls: type[_PluginCoT], /) -> None:
        super()._set_cls(cls)
        cls.plugin = staticmethod(update_wrapper(lambda: self, cls.plugin))  # ty:ignore[unresolved-attribute]
