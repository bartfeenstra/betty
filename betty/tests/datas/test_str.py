import pytest

from betty.datas.str import StrDefinition
from betty.user.error import UserFacingError


class TestStrDefinition:
    def test_load(self) -> None:
        value = "Hello, world!"
        sut = StrDefinition(label="-")
        assert sut.porter.load(value) == value

    def test_load__without_str(self) -> None:
        sut = StrDefinition(label="-")
        with pytest.raises(UserFacingError):
            assert sut.porter.load({})

    def test_dump(self) -> None:
        value = "Hello, world!"
        sut = StrDefinition(label="-")
        assert sut.porter.dump(value) == value
