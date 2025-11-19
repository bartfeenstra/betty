"""
Test utilities for :py:mod:`betty.plugin`.
"""

from __future__ import annotations

from typing import Any, ClassVar, final

import pytest
from typing_extensions import override

from betty.config import DefaultConfigurable
from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import assert_machine_name
from betty.plugin import (
    ClassedPluginDefinition,
    CountableHumanFacingPluginDefinition,
    HumanFacingPluginDefinition,
    PluginDefinition,
    PluginTypeDefinition,
)
from betty.plugin.discovery.callback import CallbackDiscovery
from betty.test_utils.config import DummyConfiguration


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


class ClassedPluginDefinitionClassTestBase(PluginDefinitionClassTestBase):
    """
    A base class for testing :py:class:`betty.plugin.ClassedPluginDefinition` subclasses.
    """

    def test_plugin_type_cls(self, sut: ClassedPluginDefinition[Any]) -> None:
        """
        Tests the :py:class:`betty.plugin.ClassedPluginDefinition`'s ``plugin_type_cls`` attribute's value.
        """
        _assert_cls_is_public(sut.plugin_type_cls)


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


class HumanFacingPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.HumanFacingPluginDefinition` subclasses.
    """

    def test_label(self, sut: HumanFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.HumanFacingPluginDefinition.label` value.
        """
        assert sut.label.localize(DEFAULT_LOCALIZER)

    def test_description(self, sut: HumanFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.HumanFacingPluginDefinition.label` value.
        """
        if sut.description is not None:
            assert sut.description.localize(DEFAULT_LOCALIZER)


class CountableHumanFacingPluginDefinitionTestBase(HumanFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.CountableHumanFacingPluginDefinition` subclasses.
    """

    def test_label_plural(self, sut: CountableHumanFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.CountableHumanFacingPluginDefinition.label_plural` value.
        """
        assert sut.label_plural.localize(DEFAULT_LOCALIZER)

    @pytest.mark.parametrize(
        "count",
        range(9),
    )
    def test_label_countable(
        self, sut: CountableHumanFacingPluginDefinition, count: int
    ) -> None:
        """
        Tests the :py:attr:`betty.plugin.CountableHumanFacingPluginDefinition.label_countable` value.
        """
        assert sut.label_countable.count(count).localize(DEFAULT_LOCALIZER)


class ClassedPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.ClassedPluginDefinition` subclasses.
    """

    def test_cls(self, sut: ClassedPluginDefinition[Any]) -> None:
        """
        Tests the :py:attr:`betty.plugin.ClassedPluginDefinition.cls` value.
        """
        _assert_cls_is_public(sut.cls)


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


class ClassedDummyPlugin:
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
        label=Plain("Classed dummy plugin"),
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


class ConfigurableDummyPlugin(DefaultConfigurable[DummyConfiguration]):
    """
    A configurable dummy plugin.
    """

    plugin: ClassVar[ConfigurableDummyPluginDefinition]

    def __init__(self):
        super().__init__(configuration=self.new_default_configuration())

    @override
    @classmethod
    def new_default_configuration(cls) -> DummyConfiguration:
        return DummyConfiguration()


class ConfigurableDummyPluginDefinition(
    ClassedPluginDefinition[ConfigurableDummyPlugin]
):
    """
    A definition of a configurable dummy plugin.
    """

    plugin_type_cls = ConfigurableDummyPlugin
    type = PluginTypeDefinition(
        id="configurable-dummy-plugin",
        label=Plain("Configurable dummy plugin"),
        discoveries=CallbackDiscovery(
            lambda: [
                ConfigurableDummyPluginOne.plugin,
            ]
        ),
    )


@final
@ConfigurableDummyPluginDefinition(
    id="configurable-dummy-plugin-one",
)
class ConfigurableDummyPluginOne(ConfigurableDummyPlugin):
    """
    A configurable dummy plugin (one).
    """
