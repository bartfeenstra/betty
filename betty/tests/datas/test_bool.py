import pytest

from betty.datas.bool import BoolDefinition
from betty.exception import HumanFacingException


class TestBoolDefinition:
    def test_load(self) -> None:
        value = True
        sut = BoolDefinition(label="-")
        assert sut.porter.load(value) is value

    def test_load__without_bool(self) -> None:
        sut = BoolDefinition(label="-")
        with pytest.raises(HumanFacingException):
            assert sut.porter.load({})

    def test_dump(self) -> None:
        value = True
        sut = BoolDefinition(label="-")
        assert sut.porter.dump(value) is value
