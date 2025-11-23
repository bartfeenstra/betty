from typing import Self

import pytest
from typing_extensions import override

from betty.factory import FactoryError, IndependentFactory, new


class _TargetType:
    pass


class TestFactoryError:
    def test_new(self) -> None:
        sut = FactoryError(self.__class__)
        assert str(sut)


class _IndependentFactoryTargetType(_TargetType, IndependentFactory):
    @override
    @classmethod
    async def new(cls) -> Self:
        return cls()


class _TargetTypeRaisesError:
    def __init__(self):
        raise RuntimeError


def _sync_callable_target() -> _TargetType:
    return _TargetType()


async def _async_callable_target() -> _TargetType:
    return _TargetType()


async def test_new__with_independent_factory() -> None:
    await new(_IndependentFactoryTargetType)


async def test_new__with_class() -> None:
    assert isinstance(await new(_TargetType), _TargetType)


async def test_new__with_class_raises_error() -> None:
    with pytest.raises(FactoryError):
        await new(_TargetTypeRaisesError)


async def test_new__with_sync_callable() -> None:
    assert isinstance(await new(_sync_callable_target), _TargetType)


async def test_new__with_async_callable() -> None:
    assert isinstance(await new(_async_callable_target), _TargetType)
