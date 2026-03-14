from __future__ import annotations

from betty.machine_name import MachineName
from betty.plugin.ordered import OrderedPluginDefinition


class TestOrderedPluginDefinition:
    def test_before(self) -> None:
        other = MachineName("other")
        sut = OrderedPluginDefinition("my-first-plugin", before={other})
        assert sut.before(other)
        assert not sut.before(MachineName("another"))

    def test_after(self) -> None:
        other = MachineName("comes-after")
        sut = OrderedPluginDefinition("my-first-plugin", after={other})
        assert sut.after(other)
        assert not sut.after(MachineName("another"))
