from __future__ import annotations

from betty.data import DataDefinition
from betty.datas.bool import BoolDefinition
from betty.datas.optional import OptionalDefinition
from betty.portable import OptionalPorter
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.tests.test_data import _DummyData


class TestOptionalDefinition:
    def test_wrapped(self) -> None:
        wrapped = BoolDefinition(label=DUMMY_LOCALIZABLE)
        sut = OptionalDefinition(wrapped)
        assert sut.wrapped is wrapped

    def test_porter(self) -> None:
        sut = OptionalDefinition(
            DataDefinition(cls=_DummyData, label=DUMMY_LOCALIZABLE)
        )
        assert isinstance(sut.porter, OptionalPorter)
