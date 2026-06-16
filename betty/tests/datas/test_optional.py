from __future__ import annotations

from betty.data import DataDefinition
from betty.datas.optional import OptionalDefinition
from betty.portable import OptionalPorter
from betty.tests.test_data import _DummyData


class TestOptionalDefinition:
    def test_porter(self) -> None:
        sut = OptionalDefinition(DataDefinition(cls=_DummyData, label="-"))
        assert isinstance(sut.porter, OptionalPorter)
