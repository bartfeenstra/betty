import pytest

from betty.datas.str import StrDefinition
from betty.exception import HumanFacingException
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestStrDefinition:
    def test_load(self) -> None:
        value = "Hello, world!"
        sut = StrDefinition(label=DUMMY_LOCALIZABLE)
        assert sut.porter.load(value) == value

    def test_load__without_str(self) -> None:
        sut = StrDefinition(label=DUMMY_LOCALIZABLE)
        with pytest.raises(HumanFacingException):
            assert sut.porter.load({})

    def test_dump(self) -> None:
        value = "Hello, world!"
        sut = StrDefinition(label=DUMMY_LOCALIZABLE)
        assert sut.porter.dump(value) == value
