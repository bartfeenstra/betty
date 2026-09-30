import pytest

from betty.datas.int import IntDefinition
from betty.user.error import UserFacingError


class TestIntDefinition:
    def test_load(self) -> None:
        value = 123
        sut = IntDefinition(label="-")
        assert sut.porter.load(value) == value

    def test_load__without_int(self) -> None:
        sut = IntDefinition(label="-")
        with pytest.raises(UserFacingError):
            assert sut.porter.load({})

    def test_dump(self) -> None:
        value = 123
        sut = IntDefinition(label="-")
        assert sut.porter.dump(value) == value
