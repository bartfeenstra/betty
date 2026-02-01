"""
Classed plugins.
"""

from __future__ import annotations

from functools import update_wrapper

from typing_extensions import TypeVar, override

from betty.definition.cls import ClsDefinition
from betty.plugin import Plugin, PluginDefinition

_PluginCoT = TypeVar("_PluginCoT", default=Plugin, covariant=True)


class PluginClsDefinition(PluginDefinition, ClsDefinition[_PluginCoT]):
    """
    A classed plugin definition.
    """

    @override
    def _set_cls(self, cls: type[_PluginCoT]) -> None:
        super()._set_cls(cls)
        cls.plugin = staticmethod(update_wrapper(lambda: self, cls.plugin))  # ty:ignore[unresolved-attribute]
