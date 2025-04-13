"""
Test utilities for :py:mod:`betty.plugin`.
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from typing_extensions import override

from betty.locale.localizable import Localizable, plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin import Plugin
from betty.string import camel_case_to_kebab_case

_PluginT = TypeVar("_PluginT", bound=Plugin)


def assert_plugin_identifier(value: Any, plugin_type: type[_PluginT]) -> None:
    """
    Assert that something is a plugin identifier.
    """
    if isinstance(value, str):
        assert_machine_name()(value)
    else:
        assert issubclass(value, plugin_type)


class PluginTestBase(Generic[_PluginT]):
    """
    A base class for testing :py:class:`betty.plugin.Plugin` implementations.
    """

    def get_sut_class(self) -> type[_PluginT]:
        """
        Produce the class of the plugin under test.
        """
        raise NotImplementedError

    async def test_class_is_public(self) -> None:
        """
        Tests that the plugin class is public.
        """
        assert not self.get_sut_class().__name__.startswith("_"), (
            f"Failed asserting that plugin class {self.get_sut_class()} is public (its name must not start with an underscore)"
        )

    async def test_plugin_id(self) -> None:
        """
        Tests :py:meth:`betty.plugin.Plugin.plugin_id` implementations.
        """
        assert_machine_name()(self.get_sut_class().plugin_id())

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


class PluginInstanceTestBase(Generic[_PluginT], PluginTestBase[_PluginT]):
    """
    A base class for testing :py:class:`betty.plugin.Plugin` implementation instances.
    """

    def get_sut_instances(self) -> Sequence[_PluginT]:
        """
        Produce instances of the plugin under test.
        """
        raise NotImplementedError


class DummyPlugin(Plugin):
    """
    A dummy plugin implementation.
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return camel_case_to_kebab_case(cls.__name__.strip("_"))

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return plain(cls.__name__)
