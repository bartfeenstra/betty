import builtins
import sys
from typing import Any

import pytest

from betty.typing import (
    FrozenDict,
    Unreachable,
    is_runtime_checkable_mapping,
    is_runtime_checkable_sequence,
)


class TestUnreachable:
    def test(self) -> None:
        assert str(Unreachable())

    def test__with_reason(self) -> None:
        assert ", because I did an oopsie." in str(Unreachable("I did an oopsie"))


class TestFrozenDict:
    def test___getitem____with_unknown_key(self) -> None:
        with pytest.raises(KeyError):
            FrozenDict()["unknown-key"]

    def test___getitem____with_known_key(self) -> None:
        assert (
            FrozenDict({"my-first-key": "My first value"})["my-first-key"]
            == "My first value"
        )

    def test___hash__(self) -> None:
        assert hash(FrozenDict()) == hash(FrozenDict())
        assert hash(FrozenDict({"my-first-key": "My first value"})) == hash(
            FrozenDict({"my-first-key": "My first value"})
        )
        assert hash(FrozenDict()) != hash(
            FrozenDict({"my-first-key": "My first value"})
        )

    def test___iter__(self) -> None:
        assert list(
            iter(FrozenDict({"my-first-key": None, "my-second-key": None}))
        ) == ["my-first-key", "my-second-key"]

    def test___len__(self) -> None:
        assert len(FrozenDict({"my-first-key": None, "my-second-key": None})) == 2

    def test___or____with_dict(self) -> None:
        assert FrozenDict({"my-shared-key": 0, "my-first-key": 1}) | {
            "my-shared-key": -1,
            "my-second-key": 2,
        } == FrozenDict({"my-shared-key": -1, "my-first-key": 1, "my-second-key": 2})

    @pytest.mark.skipif(
        sys.version_info < (3, 15), reason="frozendict was introduced in Python 3.15"
    )
    def test___or____with_frozendict(self) -> None:
        assert FrozenDict({
            "my-shared-key": 0,
            "my-first-key": 1,
        }) | builtins.frozendict({  # ty: ignore[unresolved-attribute]
            "my-shared-key": -1,
            "my-second-key": 2,
        }) == FrozenDict({"my-shared-key": -1, "my-first-key": 1, "my-second-key": 2})

    def test___or____with_frozen_dict(self) -> None:
        assert FrozenDict({"my-shared-key": 0, "my-first-key": 1}) | FrozenDict({
            "my-shared-key": -1,
            "my-second-key": 2,
        }) == FrozenDict({"my-shared-key": -1, "my-first-key": 1, "my-second-key": 2})

    def test_fromkeys__without_value(self) -> None:
        assert FrozenDict.fromkeys(("my-first-key", "my-second-key")) == FrozenDict({
            "my-first-key": None,
            "my-second-key": None,
        })

    def test_fromkeys__with_value(self) -> None:
        assert FrozenDict.fromkeys(
            ("my-first-key", "my-second-key"), 123
        ) == FrozenDict({"my-first-key": 123, "my-second-key": 123})

    def test_reversed(self) -> None:
        assert list(
            FrozenDict({"my-first-key": None, "my-second-key": None}).reversed()
        ) == ["my-second-key", "my-first-key"]


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
