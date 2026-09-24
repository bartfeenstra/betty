from __future__ import annotations

from typing import Any

import pytest

from betty.definition import (
    Definition,
    DefinitionClassVar,
    HasDefinition,
    ResolvableDefinition,
    resolve_definition,
)
from betty.test_utils.plugin import DummyPluginOne


@pytest.mark.parametrize(
    "plugin_definition",
    [
        DummyPluginOne.definition,
        DummyPluginOne,
    ],
)
def test_resolve_definition__with_valid_plugin_definition(
    plugin_definition: ResolvableDefinition,
) -> None:

    assert resolve_definition(plugin_definition) is DummyPluginOne.definition


@pytest.mark.parametrize(
    "plugin_definition",
    [
        "",
        object(),
        None,
    ],
)
def test_resolve_definition__with_invalid_plugin_definition(
    plugin_definition: Any,
) -> None:
    with pytest.raises(
        ValueError,  # noqa: PT011
    ):
        resolve_definition(plugin_definition)


class TestDefinitionClassVar:
    def test___get__(self) -> None:
        definition = Definition()

        class _Owner(HasDefinition):
            my_first_definition = DefinitionClassVar(definition)

        assert _Owner.my_first_definition is definition
        assert _Owner().my_first_definition is definition
