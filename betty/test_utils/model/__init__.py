"""
Test utilities for :py:mod:`betty.model`.
"""

from __future__ import annotations

from betty.locale.localizable import Localizable, plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import Entity
from betty.test_utils.plugin import DummyPlugin, PluginTestBase
from typing_extensions import override


class EntityTestBase(PluginTestBase[Entity]):
    """
    A base class for testing :py:class:`betty.plugin.Plugin` implementations.
    """

    async def test_plugin_label_plural(self) -> None:
        """
        Tests :py:meth:`betty.model.Entity.plugin_label_plural` implementations.
        """
        assert self.get_sut_class().plugin_label_plural().localize(DEFAULT_LOCALIZER)


class DummyEntity(DummyPlugin, Entity):
    """
    A dummy plugin implementation.
    """

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return plain(cls.__name__)
