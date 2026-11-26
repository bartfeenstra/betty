from __future__ import annotations

from betty.definition.id import IdentifiableDefinition, resolve_id
from betty.machine_name import MachineName
from betty.test_utils.plugin import DummyPluginOne


class TestIdentifiableDefinition:
    def test_id(self) -> None:
        assert IdentifiableDefinition(id="hello-world").id == MachineName("hello-world")


def test_resolve_id() -> None:
    assert resolve_id(str(DummyPluginOne.definition.id)) == DummyPluginOne.definition.id
    assert resolve_id(DummyPluginOne.definition.id) == DummyPluginOne.definition.id
    assert resolve_id(DummyPluginOne.definition) == DummyPluginOne.definition.id
    assert resolve_id(DummyPluginOne) == DummyPluginOne.definition.id
