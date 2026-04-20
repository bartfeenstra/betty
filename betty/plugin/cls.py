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

    Classed plugins may optionally subclass this class to expose their plugin definitions.
    """

    @classmethod
    def plugin(cls) -> PluginClsDefinitionT:
        """
        The plugin definition.
        """
        raise NotImplementedError(
            f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(PluginClsDefinition)} subclass."
        )


_PluginClsCoT = TypeVar("_PluginClsCoT", covariant=True)


class PluginClsDefinition(PluginDefinition, ClsDefinition[_PluginClsCoT]):
    """
    A classed plugin definition.
    """

    @override
    def _set_cls(self, cls: type[_PluginClsCoT], /) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Plugin):
            cls.plugin = staticmethod(update_wrapper(lambda: self, cls.plugin))  # ty:ignore[invalid-assignment]
