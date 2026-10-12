from typing import Any, final, override

import pytest
from pytest_mock import MockerFixture
from typing_extensions import sentinel

from betty.frosty import (
    Freezable,
    Frosty,
    FrozenAlready,
    NeitherFrozenNorFreezable,
    freeze,
    is_frozen,
)


@final
class _Frozen(Frosty):
    @override
    @property
    def is_frozen(self) -> bool:
        return True


@final
class _NotFrozen(Frosty):
    @override
    @property
    def is_frozen(self) -> bool:
        return False


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
    with pytest.raises(NeitherFrozenNorFreezable):
        freeze(value)


@pytest.mark.parametrize("value", _frozen_values)
def test_freeze__with_frozen(value: Any) -> None:
    assert freeze(value) is value
    assert is_frozen(value)


def test_freeze__with_freezable(mocker: MockerFixture) -> None:
    value = mocker.MagicMock(spec=Freezable)
    assert freeze(value) is value
    value.freeze.assert_called_once()


class TestNeitherFrozenNorFreezable:
    def test(self) -> None:
        assert str(NeitherFrozenNorFreezable(object()))


class TestFrozenAlready:
    def test(self) -> None:
        class _Frosty(Frosty):
            @override
            @property
            def is_frozen(self) -> bool:
                return True

        assert str(FrozenAlready(_Frosty()))
