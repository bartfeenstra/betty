"""
Test utilities for :py:mod:`betty.service.plugin`.
"""

from typing import final, override

from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer
from betty.service.plugin.service import ServicePluginDefinition
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE


class DummyServicePlugin(Plugin["DummyServicePluginDefinition"]):
    """
    A dummy service plugin.
    """


@final
@PluginTypeDefinition(
    "dummy-service-plugin",
    label="Dummy service plugin",
    label_plural="Dummy service plugins",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class DummyServicePluginDefinition(ServicePluginDefinition[DummyServicePlugin]):
    """
    Define a dummy service plugin.
    """


@final
class DummyServicePluginManufacturer(
    PluginManufacturer[DummyServicePluginDefinition, DummyServicePlugin]
):
    """
    Create new dummy service plugins.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[DummyServicePluginDefinition]:
        return DummyServicePluginDefinition


@final
@DummyServicePluginDefinition("dummy-service-plugin-isolated")
class DummyServicePluginOne(DummyServicePlugin):
    """
    A dummy service plugin, one.
    """
