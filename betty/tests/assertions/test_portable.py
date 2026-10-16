from typing import Any

import pytest

from betty.assertions.portable import assert_portable_data
from betty.exception import HumanFacingException


@pytest.mark.parametrize(
    "value",
    [
        object,
        object(),
    ],
)
def test_assert_portable_data__with_invalid_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_portable_data(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        False,
        1.23,
        123,
        "",
        "abc",
        (),
        ("abc",),
        ["abc"],
        {"abc": "ABC"},
    ],
)
def test_assert_portable_data__with_valid_value(value: Any) -> None:
    assert assert_portable_data(value) == value
