"""
Test utilities for :py:mod:`betty.plugin`.
"""

from __future__ import annotations

from typing import ClassVar, final

import pytest

from betty.locale.localizable import CountablePlain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import assert_machine_name
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.callback import CallbackDiscovery


def _assert_cls_is_public(cls: type) -> None:
    assert not cls.__name__.startswith("_"), (
        f"Failed asserting that plugin class {cls} is public (its name must not start with an underscore)"
    )


class PluginDefinitionClassTestBase:
    """
    A base class for testing :py:class:`betty.plugin.PluginDefinition` subclasses.
    """

    @pytest.fixture
    def sut(self) -> type[PluginDefinition]:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    def test_plugin_type_cls(self, sut: PluginDefinition) -> None:
        """
        Tests the :py:class:`betty.plugin.PluginDefinition`'s ``plugin_type_cls`` attribute's value.
        """
        _assert_cls_is_public(sut.plugin_type_cls)

    def test_type__id(self, sut: PluginDefinition) -> None:
        """
        Tests the :py:class:`betty.plugin.PluginDefinition`'s ``type`` attribute's ``id`` value.
        """
        assert_machine_name()(sut.type.id)

    def test_type__label(self, sut: PluginDefinition) -> None:
        """
        Tests the :py:class:`betty.plugin.PluginDefinition`'s ``type`` attribute's ``label`` value.
        """
        assert sut.type.label.localize(DEFAULT_LOCALIZER)


class PluginDefinitionTestBase:
    """
    A base class for testing :py:class:`betty.plugin.PluginDefinition` subclasses.
    """

    @pytest.fixture
    def sut(self) -> PluginDefinition:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    def test_id(self, sut: PluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.PluginDefinition.id` value.
        """
        assert_machine_name()(sut.id)

    def test_cls(self, sut: PluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.PluginDefinition.cls` value.
        """
        _assert_cls_is_public(sut.cls)


class DummyPlugin(Plugin):
    """
    A dummy plugin.
    """

    plugin: ClassVar[DummyPluginDefinition]


class DummyPluginDefinition(PluginDefinition[DummyPlugin]):
    """
    A definition of a dummy plugin.
    """

    plugin_type_cls = DummyPlugin
    type = PluginTypeDefinition(
        "dummy-plugin",
        " dummy plugin",
        " dummy plugin",
        CountablePlain("{count} dummy plugin", "{count} dummy plugins"),
        discoveries=CallbackDiscovery(
            lambda: [
                DummyPluginOne.plugin,
                DummyPluginTwo.plugin,
                DummyPluginThree.plugin,
                DummyPluginFour.plugin,
            ]
        ),
    )


@final
@DummyPluginDefinition("dummy-plugin-one")
class DummyPluginOne(DummyPlugin):
    """
    A dummy plugin (one).
    """


@final
@DummyPluginDefinition("dummy-plugin-two")
class DummyPluginTwo(DummyPlugin):
    """
    A dummy plugin (two).
    """


@final
@DummyPluginDefinition("dummy-plugin-three")
class DummyPluginThree(DummyPlugin):
    """
    A dummy plugin (three).
    """


@final
@DummyPluginDefinition("dummy-plugin-four")
class DummyPluginFour(DummyPlugin):
    """
    A dummy plugin (four).
    """
