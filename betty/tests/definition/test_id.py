from __future__ import annotations

from typing import Any

import pytest

from betty.definition.id import IdentifiableDefinition, ResolvableId, resolve_id
from betty.machine_name import MachineName
from betty.test_utils.plugin import DummyPluginOne


class TestIdentifiableDefinition:
    def test_id(self) -> None:
        assert IdentifiableDefinition(id="hello-world").id == MachineName("hello-world")


@pytest.mark.parametrize(
    "plugin_id",
    [
        str(DummyPluginOne.definition.id),
        DummyPluginOne.definition.id,
        DummyPluginOne.definition,
        DummyPluginOne,
    ],
)
def test_resolve_id__with_valid_plugin_id(
    plugin_id: ResolvableId,
) -> None:
    assert resolve_id(plugin_id) == DummyPluginOne.definition.id


@pytest.mark.parametrize(
    "plugin_id",
    [
        "",
        object(),
        None,
    ],
)
def test_resolve_id__with_invalid_plugin_id(plugin_id: Any) -> None:
    with pytest.raises(
        ValueError,  # noqa: PT011
    ):
        resolve_id(plugin_id)
