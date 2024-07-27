"""
Test utilities for :py:module:`betty.model`.
"""

from __future__ import annotations

from typing_extensions import override

from betty.locale.localizable import Localizable, static
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import Entity
from betty.test_utils.plugin import DummyPlugin, PluginTestBase


class EntityTestBase(PluginTestBase[Entity]):
    """
    A base class for testing :py:class:`betty.plugin.Plugin` implementations.
    """

    async def test_plugin_label_plural(self) -> None:
        """
        Tests :py:meth:`betty.plugin.Plugin.plugin_label_plural` implementations.
        """
        assert self.get_sut_class().plugin_label_plural().localize(DEFAULT_LOCALIZER)


class DummyEntity(DummyPlugin, Entity):
    """
    A dummy plugin implementation.
    """

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return static(cls.__name__)
