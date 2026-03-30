from __future__ import annotations

from typing import Any

import pytest

from betty.plugin.resolve import (
    ResolvablePluginDefinition,
    ResolvablePluginId,
    ResolvablePluginTypeId,
    resolve_plugin_definition,
    resolve_plugin_id,
    resolve_plugin_type_id,
)
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


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
