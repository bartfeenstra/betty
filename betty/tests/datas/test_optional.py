from __future__ import annotations

from betty.data import DataDefinition
from betty.datas.optional import OptionalDefinition
from betty.porters.optional import OptionalPorter


class TestOptionalDefinition:
    def test_porter(self) -> None:
        sut = OptionalDefinition(DataDefinition(label="-"))
        assert isinstance(sut.try_porter, OptionalPorter)
