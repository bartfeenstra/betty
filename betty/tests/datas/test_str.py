import pytest

from betty.datas.str import StrDefinition
from betty.validators.str import NotAStr


class TestStrDefinition:
    def test_load(self) -> None:
        value = "Hello, world!"
        sut = StrDefinition(label="-")
        assert sut.porter.load(value) == value

    def test_load__without_str(self) -> None:
        sut = StrDefinition(label="-")
        with pytest.raises(NotAStr):
            assert sut.porter.load({})

    def test_dump(self) -> None:
        value = "Hello, world!"
        sut = StrDefinition(label="-")
        assert sut.porter.dump(value) == value
