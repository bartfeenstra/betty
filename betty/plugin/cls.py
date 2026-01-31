"""
Classed plugins.
"""

from __future__ import annotations

from functools import update_wrapper

from typing_extensions import TypeVar, override

from betty.definition.cls import ClsDefinition
from betty.plugin import Plugin, PluginDefinition

_PluginT = TypeVar("_PluginT", default=Plugin)


class PluginClsDefinition(PluginDefinition, ClsDefinition[_PluginT]):
    """
    A classed plugin definition.
    """

    @override
    def _set_cls(self, cls: type[_PluginT]) -> None:
        super()._set_cls(cls)
        cls.plugin = staticmethod(update_wrapper(lambda: self, cls.plugin))  # ty:ignore[unresolved-attribute]
