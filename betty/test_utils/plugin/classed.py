"""
Test utilities for :py:mod:`betty.plugin.classed`.
"""

from __future__ import annotations

from typing import Any, ClassVar, final

from betty.plugin import PluginTypeDefinition
from betty.plugin.classed import ClassedPlugin, ClassedPluginDefinition
from betty.plugin.discovery.callback import CallbackDiscovery
from betty.test_utils.plugin import (
    PluginDefinitionClassTestBase,
    PluginDefinitionTestBase,
)


class ClassedDummyPlugin(ClassedPlugin):
    """
    A classed dummy plugin.
    """

    plugin: ClassVar[ClassedDummyPluginDefinition]


class ClassedDummyPluginDefinition(ClassedPluginDefinition[ClassedDummyPlugin]):
    """
    A definition of a classed dummy plugin.
    """

    plugin_type_cls = ClassedDummyPlugin
    type = PluginTypeDefinition(
        id="classed-dummy-plugin",
        label="Classed dummy plugin",
        discoveries=CallbackDiscovery(
            lambda: [
                ClassedDummyPluginOne.plugin,
                ClassedDummyPluginTwo.plugin,
            ]
        ),
    )


@final
@ClassedDummyPluginDefinition(
    id="classed-dummy-plugin-one",
)
class ClassedDummyPluginOne(ClassedDummyPlugin):
    """
    A classed dummy plugin (one).
    """


@final
@ClassedDummyPluginDefinition(
    id="classed-dummy-plugin-two",
)
class ClassedDummyPluginTwo(ClassedDummyPlugin):
    """
    A classed dummy plugin (two).
    """


class ClassedPluginDefinitionClassTestBase(PluginDefinitionClassTestBase):
    """
    A base class for testing :py:class:`betty.plugin.classed.ClassedPluginDefinition` subclasses.
    """

    def test_plugin_type_cls(self, sut: ClassedPluginDefinition[Any]) -> None:
        """
        Tests the :py:class:`betty.plugin.classed.ClassedPluginDefinition`'s ``plugin_type_cls`` attribute's value.
        """
        _assert_cls_is_public(sut.plugin_type_cls)


class ClassedPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.classed.ClassedPluginDefinition` subclasses.
    """

    def test_cls(self, sut: ClassedPluginDefinition[Any]) -> None:
        """
        Tests the :py:attr:`betty.plugin.classed.ClassedPluginDefinition.cls` value.
        """
        _assert_cls_is_public(sut.cls)


def _assert_cls_is_public(cls: type) -> None:
    assert not cls.__name__.startswith("_"), (
        f"Failed asserting that plugin class {cls} is public (its name must not start with an underscore)"
    )
