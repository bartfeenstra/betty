import pytest

from betty.datas.int import IntDefinition
from betty.exception import HumanFacingException
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestIntDefinition:
    def test_load(self) -> None:
        value = 123
        sut = IntDefinition(label=DUMMY_LOCALIZABLE)
        assert sut.porter.load(value) == value

    def test_load__without_int(self) -> None:
        sut = IntDefinition(label=DUMMY_LOCALIZABLE)
        with pytest.raises(HumanFacingException):
            assert sut.porter.load({})

    def test_dump(self) -> None:
        value = 123
        sut = IntDefinition(label=DUMMY_LOCALIZABLE)
        assert sut.porter.dump(value) == value
