from typing import Any, override

import pytest
from pytest_mock import MockerFixture
from typing_extensions import sentinel

from betty.frozen import (
    Freezable,
    FreezableClassVar,
    FrozenAlready,
    NotFreezable,
    NotYetFrozen,
    freeze,
    is_frozen,
)


class _Frozen(Freezable):
    @override
    @property
    def is_frozen(self) -> bool:
        return True


class _NotFrozen(Freezable):
    @override
    @property
    def is_frozen(self) -> bool:
        return False


class TestNotFreezable:
    def test(self) -> None:
        assert str(NotFreezable(object()))


class TestNotYetFrozen:
    def test(self) -> None:
        assert str(NotYetFrozen(_NotFrozen()))


class TestFrozenAlready:
    def test(self) -> None:
        assert str(FrozenAlready(_Frozen()))


_frozen_values = (
    None,
    True,
    False,
    1.23,
    123,
    frozenset(),
    sentinel("my_first_sentinel"),
    (1, 2, 3, object),
    _Frozen(),
    "My First String",
)
_not_freezable_values = (object(),)
_not_frozen_values = (
    *_not_freezable_values,
    _NotFrozen(),
)


@pytest.mark.parametrize("value", _not_frozen_values)
def test_is_frozen__without_frozen(value: Any) -> None:
    assert not is_frozen(value)


@pytest.mark.parametrize("value", _frozen_values)
def test_is_frozen__with_frozen(value: Any) -> None:
    assert is_frozen(value)


@pytest.mark.parametrize("value", _not_freezable_values)
def test_freeze__without_freezable(value: Any) -> None:
    with pytest.raises(NotFreezable):
        freeze(value)


@pytest.mark.parametrize("value", _frozen_values)
def test_freeze__with_frozen(value: Any) -> None:
    freeze(value)
    assert is_frozen(value)


def test_freeze__with_freezable(mocker: MockerFixture) -> None:
    value = mocker.MagicMock(spec=Freezable)
    freeze(value)
    value.freeze.assert_called_once()


class TestFreezable:
    def test_freeze__not_yet_frozen(self, mocker: MockerFixture) -> None:
        class _Sut(_NotFrozen):
            my_first_freezable_class_var = mocker.MagicMock(spec=FreezableClassVar)

        sut = _Sut()
        sut.freeze()
        _Sut.my_first_freezable_class_var.freeze.assert_called_once_with(sut)

    def test_freeze__frozen_already(self, mocker: MockerFixture) -> None:
        class _Sut(_Frozen):
            my_first_freezable_class_var = mocker.MagicMock(spec=FreezableClassVar)

        sut = _Sut()
        sut.freeze()
        _Sut.my_first_freezable_class_var.freeze.assert_not_called()

    def test_assert_frozen(self) -> None:
        _Frozen().assert_frozen()
        with pytest.raises(NotYetFrozen):
            _NotFrozen().assert_frozen()

    def test_assert_not_frozen(self) -> None:
        _NotFrozen().assert_not_frozen()
        with pytest.raises(FrozenAlready):
            _Frozen().assert_not_frozen()
