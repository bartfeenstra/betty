from __future__ import annotations

from typing import Any, final

import pytest

from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin import (
    Plugin,
    PluginDefinition,
    PluginTypeDefinition,
    ResolvablePluginDefinition,
    ResolvablePluginId,
    ResolvablePluginTypeId,
    resolve_plugin_definition,
    resolve_plugin_id,
    resolve_plugin_type_id,
)
from betty.plugin.ordered import OrderedPluginDefinition
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.plugin import DummyPlugin, DummyPluginDefinition, DummyPluginOne


@final
@PluginTypeDefinition(
    "ordered-plugin",
    label="_OrderedPluginDefinition",
    label_plural="_OrderedPluginDefinitions",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _OrderedPluginDefinition(OrderedPluginDefinition[DummyPlugin]):
    pass


_ORDERED_PLUGIN_COMES_BEFORE_TARGET = _OrderedPluginDefinition(
    "ordered-plugin-comes-before-target"
)

_ORDERED_PLUGIN_HAS_COMES_BEFORE = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-before",
    comes_before={_ORDERED_PLUGIN_COMES_BEFORE_TARGET},
)
_ORDERED_PLUGIN_COMES_AFTER_TARGET = _OrderedPluginDefinition(
    "ordered-plugin-comes-after-target"
)

_ORDERED_PLUGIN_HAS_COMES_AFTER = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-after", comes_after={_ORDERED_PLUGIN_COMES_AFTER_TARGET}
)

_ORDERED_PLUGIN_ISOLATED = _OrderedPluginDefinition("ordered-plugin-isolated")


_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-before-bidirectional",
    comes_before={"ordered-plugin-has-comes-after-bidirectional"},
)
_ORDERED_PLUGIN_HAS_COMES_AFTER_BIDIRECTIONAL = _OrderedPluginDefinition(
    "ordered-plugin-has-comes-after-bidirectional",
    comes_after={_ORDERED_PLUGIN_HAS_COMES_BEFORE_BIDIRECTIONAL},
)


class TestPluginTypeDefinition:
    def test_id(self) -> None:
        plugin_type_id = "my-first-plugin-type"
        sut = PluginTypeDefinition(
            plugin_type_id,
            label=DUMMY_LOCALIZABLE,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.id == plugin_type_id


class TestPluginDefinition:
    def test_id(self) -> None:
        id = "my-first-plugin"  # noqa: A001
        sut = PluginDefinition(id)
        assert sut.id == id

    def test_reference_label(self) -> None:
        id = "my-first-plugin"  # noqa: A001
        sut = PluginDefinition(id)
        actual = sut.reference_label.localize(DEFAULT_LOCALIZER)
        assert id in actual

    def test_reference_label_with_type(self) -> None:
        plugin_type_label = "My First Plugin Type"

        @final
        @PluginTypeDefinition(
            "my-first-plugin-type",
            label=plugin_type_label,
            label_plural=DUMMY_LOCALIZABLE,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        class _PluginDefinition(PluginDefinition[DummyPlugin]):
            pass

        id = "my-first-plugin"  # noqa: A001
        sut = _PluginDefinition(id)
        actual = sut.reference_label_with_type.localize(DEFAULT_LOCALIZER)
        assert id in actual
        assert plugin_type_label in actual


class _PluginCls(Plugin["_PluginDefinition"]):
    pass


@final
@PluginTypeDefinition(
    "-dummy",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _PluginDefinition(PluginDefinition[_PluginCls]):
    pass


@pytest.mark.parametrize(
    "plugin_type_id",
    [
        str(DummyPluginDefinition.type().id),
        DummyPluginDefinition.type().id,
        DummyPluginDefinition.type(),
        DummyPluginDefinition,
        DummyPluginOne,
    ],
)
def test_resolve_plugin_type_id__with_valid_plugin_type_id(
    plugin_type_id: ResolvablePluginTypeId,
) -> None:
    assert resolve_plugin_type_id(plugin_type_id) == DummyPluginDefinition.type().id


@pytest.mark.parametrize(
    "plugin_type_id",
    [
        "",
        object(),
        None,
    ],
)
def test_resolve_plugin_type_id__with_invalid_plugin_type_id(
    plugin_type_id: Any,
) -> None:
    with pytest.raises(
        ValueError,  # noqa:PT011
    ):
        resolve_plugin_type_id(plugin_type_id)


@pytest.mark.parametrize(
    "plugin_definition",
    [
        DummyPluginOne.plugin(),
        DummyPluginOne,
    ],
)
def test_resolve_plugin_definition__with_valid_plugin_definition(
    plugin_definition: ResolvablePluginDefinition,
) -> None:

    assert resolve_plugin_definition(plugin_definition) is DummyPluginOne.plugin()


@pytest.mark.parametrize(
    "plugin_definition",
    [
        "",
        object(),
        None,
    ],
)
def test_resolve_plugin_definition__with_invalid_plugin_definition(
    plugin_definition: Any,
) -> None:
    with pytest.raises(
        ValueError,  # noqa: PT011
    ):
        resolve_plugin_definition(plugin_definition)


@pytest.mark.parametrize(
    "plugin_id",
    [
        str(DummyPluginOne.plugin().id),
        DummyPluginOne.plugin().id,
        DummyPluginOne.plugin(),
        DummyPluginOne,
    ],
)
def test_resolve_plugin_id__with_valid_plugin_id(plugin_id: ResolvablePluginId) -> None:
    assert resolve_plugin_id(plugin_id) == DummyPluginOne.plugin().id


@pytest.mark.parametrize(
    "plugin_id",
    [
        "",
        object(),
        None,
    ],
)
def test_resolve_plugin_id__with_invalid_plugin_id(plugin_id: Any) -> None:
    with pytest.raises(
        ValueError,  # noqa: PT011
    ):
        resolve_plugin_id(plugin_id)
