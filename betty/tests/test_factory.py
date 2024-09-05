import pytest
from betty.factory import FactoryError, new


class TestFactoryError:
    def test_new(self) -> None:
        sut = FactoryError.new(self.__class__)
        assert str(sut)


class _New:
    pass


class _NewRaisesError:
    def __init__(self):
        raise RuntimeError


class TestNew:
    def test(self) -> None:
        new(_New)

    def test_with___init___error(self) -> None:
        with pytest.raises(FactoryError):
            new(_NewRaisesError)
