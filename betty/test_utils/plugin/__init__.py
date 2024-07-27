"""
Test utilities for :py:module:`betty.plugin`.
"""

from abc import ABC, abstractmethod
from typing_extensions import override

from betty.locale.localizable import Localizable, static
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import assert_machine_name, MachineName
from betty.plugin import Plugin
from betty.string import camel_case_to_kebab_case


class PluginTestBase(ABC):
    """
    A base class for testing :py:class:`betty.plugin.Plugin` implementations.
    """

    @abstractmethod
    def get_sut_class(self) -> type[Plugin]:
        """
        Produce the class of the plugin under test.
        """
        pass

    async def test_plugin_id(self) -> None:
        """
        Tests :py:meth:`betty.plugin.Plugin.plugin_id` implementations.
        """
        assert_machine_name(self.get_sut_class().plugin_id())

    async def test_plugin_label(self) -> None:
        """
        Tests :py:meth:`betty.plugin.Plugin.plugin_label` implementations.
        """
        assert self.get_sut_class().plugin_label().localize(DEFAULT_LOCALIZER)

    async def test_plugin_description(self) -> None:
        """
        Tests :py:meth:`betty.plugin.Plugin.plugin_description` implementations.
        """
        description = self.get_sut_class().plugin_description()
        if description is not None:
            assert description.localize(DEFAULT_LOCALIZER)


class DummyPlugin(Plugin):
    """
    A dummy plugin implementation.
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return camel_case_to_kebab_case(cls.__name__)

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return static(cls.__name__)
