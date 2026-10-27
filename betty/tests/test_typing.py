from typing import Any

import pytest

from betty.collections.mapping.dict import FrozenDict
from betty.typing import (
    Unreachable,
    is_runtime_checkable_mapping,
    is_runtime_checkable_sequence,
)


class TestUnreachable:
    def test(self) -> None:
        assert str(Unreachable())

    def test__with_reason(self) -> None:
        assert ", because I did an oopsie." in str(Unreachable("I did an oopsie"))


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (True, ()),
        (True, (False,)),
        (True, []),
        (True, [False]),
        (False, object),
        (False, object()),
        (False, FrozenDict()),
        (False, {}),
    ],
)
def test_is_runtime_checkable_sequence(expected: bool, value: Any) -> None:
    assert is_runtime_checkable_sequence(value) is expected


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (True, FrozenDict()),
        (True, FrozenDict({False: False})),
        (True, FrozenDict({False: {}})),
        (True, {}),
        (True, {False: False}),
        (True, {False: {}}),
        (False, object),
        (False, object()),
        (False, ()),
    ],
)
def test_is_runtime_checkable_mapping(expected: bool, value: Any) -> None:
    assert is_runtime_checkable_mapping(value) is expected
