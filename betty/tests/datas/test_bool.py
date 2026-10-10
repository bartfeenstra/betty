import pytest

from betty.datas.bool import BoolDefinition
from betty.validators.bool import NotABool


class TestBoolDefinition:
    def test_porter__load(self) -> None:
        value = True
        sut = BoolDefinition(label="-")
        assert sut.porter.load(value) is value

    def test_porter__load__without_bool(self) -> None:
        sut = BoolDefinition(label="-")
        with pytest.raises(NotABool):
            assert sut.porter.load({})

    def test_porter__dump(self) -> None:
        value = True
        sut = BoolDefinition(label="-")
        assert sut.porter.dump(value) is value
