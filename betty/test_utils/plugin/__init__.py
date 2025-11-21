"""
Test utilities for :py:mod:`betty.plugin`.
"""

from __future__ import annotations

import pytest

from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import assert_machine_name
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.callback import CallbackDiscovery


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


class DummyPluginDefinition(PluginDefinition):
    """
    A definition of a dummy plugin.
    """

    type = PluginTypeDefinition(
        id="dummy-plugin",
        label=Plain("Dummy plugin"),
        discoveries=CallbackDiscovery(
            lambda: [
                DUMMY_PLUGIN_ONE,  # type: ignore[has-type]
                DUMMY_PLUGIN_TWO,  # type: ignore[has-type]
                DUMMY_PLUGIN_THREE,  # type: ignore[has-type]
            ]
        ),
    )


DUMMY_PLUGIN_ONE = DummyPluginDefinition(
    id="dummy-plugin-one",
)

DUMMY_PLUGIN_TWO = DummyPluginDefinition(
    id="dummy-plugin-two",
)

DUMMY_PLUGIN_THREE = DummyPluginDefinition(
    id="dummy-plugin-three",
)

DUMMY_PLUGIN_FOUR = DummyPluginDefinition(
    id="dummy-plugin-four",
)
