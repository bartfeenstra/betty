from typing import Self

import pytest
from typing_extensions import override

from betty.factory import FactoryError, IndependentFactory, new


class TestFactoryError:
    def test_new(self) -> None:
        sut = FactoryError(self.__class__)
        assert str(sut)


class _NewIndependentFactory(IndependentFactory):
    def __init__(self, sentinel: None):
        pass

    @override
    @classmethod
    async def new(cls) -> Self:
        return cls(None)


class _NewInit:
    pass


class _NewInitRaisesError:
    def __init__(self):
        raise RuntimeError


async def test_new__with_independent_factory() -> None:
    await new(_NewIndependentFactory)


async def test_new__with___init__() -> None:
    await new(_NewInit)


async def test_new__with___init___error() -> None:
    with pytest.raises(FactoryError):
        await new(_NewInitRaisesError)
