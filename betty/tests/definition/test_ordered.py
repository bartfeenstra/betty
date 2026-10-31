from __future__ import annotations

from betty.definition.ordered import OrderedDefinition
from betty.machine_name import MachineName


class TestOrderedDefinition:
    def test_before(self) -> None:
        other = MachineName("other")
        sut = OrderedDefinition("my-first-plugin", before={other})
        assert sut.before(other)
        assert not sut.before(MachineName("another"))

    def test_after(self) -> None:
        other = MachineName("comes-after")
        sut = OrderedDefinition("my-first-plugin", after={other})
        assert sut.after(other)
        assert not sut.after(MachineName("another"))
