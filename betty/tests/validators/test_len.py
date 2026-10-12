from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.validators.len import TooLong, TooShort, is_len, is_max_len, is_min_len

if TYPE_CHECKING:
    from collections.abc import Sized

    from betty.validation import Invalid


class TestIsLen:
    @pytest.mark.parametrize(
        ("expected", "value"),
        [
            (0, ""),
            (3, "abc"),
            (0, []),
            (3, ["a", "b", "c"]),
            (0, {}),
            (3, {"a": 1, "b": 2, "c": 3}),
        ],
    )
    def test__validate__with_valid_value(self, expected: int, value: Sized) -> None:
        is_len(value, expected)

    @pytest.mark.parametrize(
        ("expected", "value"),
        [
            (TooShort, "a"),
            (TooLong, "abc"),
            (TooShort, ["a"]),
            (TooLong, ["a", "b", "c"]),
            (TooShort, {"a": 1}),
            (TooLong, {"a": 1, "b": 2, "c": 3}),
        ],
    )
    def test__validate__with_invalid_value(
        self, expected: type[Invalid], value: Sized
    ) -> None:
        with pytest.raises(expected):
            is_len(value, 2)


class TestIsMinLen:
    @pytest.mark.parametrize(
        ("expected", "value"),
        [
            # Minimums that match the exact length.
            (0, ""),
            (3, "abc"),
            (0, []),
            (3, ["a", "b", "c"]),
            (0, {}),
            (3, {"a": 1, "b": 2, "c": 3}),
            # Minimums that are significantly below the exact length.
            (0, "abc"),
            (0, ["a", "b", "c"]),
            (0, {"a": 1, "b": 2, "c": 3}),
        ],
    )
    def test__validate__with_valid_value(self, expected: int, value: Sized) -> None:
        is_min_len(value, expected)

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "a",
            [],
            ["a"],
            {},
            {"a": 1},
        ],
    )
    def test__validate__with_invalid_value(self, value: Sized) -> None:
        with pytest.raises(TooShort):
            is_min_len(value, 2)


class TestIsMaxLen:
    @pytest.mark.parametrize(
        ("expected", "value"),
        [
            # Maximums that match the exact length.
            (0, ""),
            (3, "abc"),
            (0, []),
            (3, ["a", "b", "c"]),
            (0, {}),
            (3, {"a": 1, "b": 2, "c": 3}),
            # Maximums that are significantly above the exact length.
            (9, "abc"),
            (9, ["a", "b", "c"]),
            (9, {"a": 1, "b": 2, "c": 3}),
        ],
    )
    def test__validate__with_valid_value(self, expected: int, value: Sized) -> None:
        is_max_len(value, expected)

    @pytest.mark.parametrize(
        "value",
        [
            "abc",
            ["a", "b", "c"],
            {"a": 1, "b": 2, "c": 3},
        ],
    )
    def test__validate__with_invalid_value(self, value: Sized) -> None:
        with pytest.raises(TooLong):
            is_max_len(value, 2)
