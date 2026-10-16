import builtins
import sys
from collections.abc import Callable
from operator import eq, is_
from typing import Any

import pytest

from betty.portable import (
    OptionalImmutablePortableData,
    OptionalMutablePortableData,
    OptionalPortableData,
    freeze_portable_data,
    is_portable_scalar,
    unfreeze_portable_data,
)
from betty.typing import FrozenDict


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (True, None),
        (True, True),
        (True, False),
        (True, 1.23),
        (True, 123),
        (False, object),
        (False, object()),
        (False, ()),
        (False, []),
        (False, {}),
    ],
)
def test_is_portable_scalar(expected: bool, value: Any) -> None:
    assert is_portable_scalar(value) is expected


@pytest.mark.parametrize(
    ("expected", "operator", "data"),
    [
        # Scalars.
        (None, is_, None),
        (True, is_, True),
        (False, is_, False),
        (1.23, eq, 1.23),
        (123, eq, 123),
        # tuple.
        ((), eq, ()),
        ((None,), eq, (None,)),
        (((None,),), eq, ((None,),)),
        (((None,),), eq, ([None],)),
        # list.
        ((), eq, []),
        ((None,), eq, [None]),
        (((None,),), eq, [[None]]),
        ((FrozenDict(),), eq, [{}]),
        # dict.
        (FrozenDict(), eq, {}),
        (FrozenDict({"my-first-key": None}), eq, {"my-first-key": None}),
        (
            FrozenDict({"my-first-key": {"my-second-key": None}}),
            eq,
            {"my-first-key": {"my-second-key": None}},
        ),
        (FrozenDict({"my-first-key": (None,)}), eq, {"my-first-key": [None]}),
        # frozendict.
        *(
            [
                (FrozenDict(), eq, builtins.frozendict()),
                (
                    FrozenDict({"my-first-key": None}),
                    eq,
                    builtins.frozendict({"my-first-key": None}),
                ),
                (
                    FrozenDict({"my-first-key": {"my-second-key": None}}),
                    eq,
                    builtins.frozendict({"my-first-key": {"my-second-key": None}}),
                ),
                (
                    FrozenDict({"my-first-key": (None,)}),
                    eq,
                    builtins.frozendict({"my-first-key": [None]}),
                ),
            ]
            if sys.version_info >= (3, 15)
            else []
        ),
        # FrozenDict.
        (FrozenDict(), eq, FrozenDict()),
        (FrozenDict({"my-first-key": None}), eq, FrozenDict({"my-first-key": None})),
        (
            FrozenDict({"my-first-key": {"my-second-key": None}}),
            eq,
            FrozenDict({"my-first-key": {"my-second-key": None}}),
        ),
        (
            FrozenDict({"my-first-key": (None,)}),
            eq,
            FrozenDict({"my-first-key": [None]}),
        ),
    ],
)
def test_freeze_portable_data(
    expected: OptionalImmutablePortableData,
    operator: Callable[
        [OptionalImmutablePortableData, OptionalImmutablePortableData], bool
    ],
    data: OptionalPortableData,
) -> None:
    assert operator(freeze_portable_data(data), expected)


@pytest.mark.parametrize(
    ("expected", "operator", "data"),
    [
        # Scalars.
        (None, is_, None),
        (True, is_, True),
        (False, is_, False),
        (1.23, eq, 1.23),
        (123, eq, 123),
        # tuple.
        ([], eq, ()),
        ([None], eq, (None,)),
        ([[None]], eq, ((None,),)),
        ([[None]], eq, ([None],)),
        # list.
        ([], eq, []),
        ([None], eq, [None]),
        ([[None]], eq, [[None]]),
        ([FrozenDict()], eq, [{}]),
        # dict.
        ({}, eq, {}),
        ({"my-first-key": None}, eq, {"my-first-key": None}),
        (
            {"my-first-key": {"my-second-key": None}},
            eq,
            {"my-first-key": {"my-second-key": None}},
        ),
        ({"my-first-key": [None]}, eq, {"my-first-key": (None,)}),
        # frozendict.
        *(
            [
                ({}, eq, builtins.frozendict()),
                (
                    {"my-first-key": None},
                    eq,
                    builtins.frozendict({"my-first-key": None}),
                ),
                (
                    {"my-first-key": {"my-second-key": None}},
                    eq,
                    builtins.frozendict({"my-first-key": {"my-second-key": None}}),
                ),
                (
                    {"my-first-key": [None]},
                    eq,
                    builtins.frozendict({"my-first-key": (None,)}),
                ),
            ]
            if sys.version_info >= (3, 15)
            else []
        ),
        # FrozenDict.
        ({}, eq, FrozenDict()),
        ({"my-first-key": None}, eq, FrozenDict({"my-first-key": None})),
        (
            {"my-first-key": {"my-second-key": None}},
            eq,
            FrozenDict({"my-first-key": {"my-second-key": None}}),
        ),
        ({"my-first-key": [None]}, eq, FrozenDict({"my-first-key": (None,)})),
    ],
)
def test_unfreeze_portable_data(
    expected: OptionalMutablePortableData,
    operator: Callable[
        [OptionalMutablePortableData, OptionalMutablePortableData], bool
    ],
    data: OptionalPortableData,
) -> None:
    assert operator(unfreeze_portable_data(data), expected)
