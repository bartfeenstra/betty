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
    ClassedPluginTypeDefinition,
    CountableUserFacingPluginDefinition,
    DependentPluginDefinition,
    OrderedPluginDefinition,
    PluginDefinition,
    PluginTypeDefinition,
    UserFacingPluginDefinition,
)
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


class UserFacingPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.UserFacingPluginDefinition` subclasses.
    """

    def test_label(self, sut: UserFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.UserFacingPluginDefinition.label` value.
        """
        assert sut.label.localize(DEFAULT_LOCALIZER)

    def test_description(self, sut: UserFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.UserFacingPluginDefinition.label` value.
        """
        if sut.description is not None:
            assert sut.description.localize(DEFAULT_LOCALIZER)


class CountableUserFacingPluginDefinitionTestBase(UserFacingPluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.CountableUserFacingPluginDefinition` subclasses.
    """

    def test_label_plural(self, sut: CountableUserFacingPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.CountableUserFacingPluginDefinition.label_plural` value.
        """
        assert sut.label_plural.localize(DEFAULT_LOCALIZER)

    @pytest.mark.parametrize(
        "count",
        range(9),
    )
    def test_label_countable(
        self, sut: CountableUserFacingPluginDefinition, count: int
    ) -> None:
        """
        Tests the :py:attr:`betty.plugin.CountableUserFacingPluginDefinition.label_countable` value.
        """
        assert sut.label_countable.count(count).localize(DEFAULT_LOCALIZER)


class OrderedPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.OrderedPluginDefinition` subclasses.
    """

    def test_comes_after(self, sut: OrderedPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.OrderedPluginDefinition.comes_after` value.
        """
        for plugin_id in sut.comes_after:
            assert_machine_name()(plugin_id)

    def test_comes_before(self, sut: OrderedPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.OrderedPluginDefinition.comes_before` value.
        """
        for plugin_id in sut.comes_before:
            assert_machine_name()(plugin_id)


class DependentPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.DependentPluginDefinition` subclasses.
    """

    def test_depends_on(self, sut: DependentPluginDefinition) -> None:
        """
        Tests the :py:attr:`betty.plugin.DependentPluginDefinition.depends_on` value.
        """
        for plugin_id in sut.depends_on:
            assert_machine_name()(plugin_id)


class ClassedPluginDefinitionTestBase(PluginDefinitionTestBase):
    """
    A base class for testing :py:class:`betty.plugin.ClassedPluginDefinition` subclasses.
    """

    def test_type__cls(self, sut: ClassedPluginDefinition[Any]) -> None:
        """
        Tests the :py:class:`betty.plugin.ClassedPluginDefinition`'s ``type`` attribute's ``cls`` value.
        """
        _assert_cls_is_public(sut.type.cls)

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

    type = ClassedPluginTypeDefinition(
        id="classed-dummy-plugin",
        label=Plain("Classed dummy plugin"),
        cls=ClassedDummyPlugin,
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

    type = ClassedPluginTypeDefinition(
        id="configurable-dummy-plugin",
        label=Plain("Configurable dummy plugin"),
        cls=ConfigurableDummyPlugin,
    )


@final
@ConfigurableDummyPluginDefinition(
    id="configurable-dummy-plugin-one",
)
class ConfigurableDummyPluginOne(ConfigurableDummyPlugin):
    """
    A configurable dummy plugin (one).
    """
