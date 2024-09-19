from typing import Self

import pytest
from typing_extensions import override

from betty.factory import FactoryError, new, IndependentFactory


class TestFactoryError:
    def test_new(self) -> None:
        sut = FactoryError.new(self.__class__)
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


class TestNew:
    async def test_with_independent_factory(self) -> None:
        await new(_NewIndependentFactory)

    async def test_with___init__(self) -> None:
        await new(_NewInit)

    async def test_with___init___error(self) -> None:
        with pytest.raises(FactoryError):
            await new(_NewInitRaisesError)
