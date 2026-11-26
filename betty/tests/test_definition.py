from __future__ import annotations

from betty.definition import (
    Definition,
    DefinitionClassVar,
    HasDefinition,
    resolve_definition,
)
from betty.test_utils.plugin import DummyPluginOne


def test_resolve_definition() -> None:

    assert resolve_definition(DummyPluginOne.definition) is DummyPluginOne.definition
    assert resolve_definition(DummyPluginOne) is DummyPluginOne.definition


class TestDefinitionClassVar:
    def test___get__(self) -> None:
        definition = Definition()

        class _Owner(HasDefinition):
            my_first_definition = DefinitionClassVar(definition)

        assert _Owner.my_first_definition is definition
        assert _Owner().my_first_definition is definition
