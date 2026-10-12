from typing import Any

import pytest

from betty.validation import Invalid
from betty.validators.portable import is_portable_data


@pytest.mark.parametrize(
    "value",
    [
        object,
        object(),
    ],
)
def test_is_portable_data__with_invalid_value(value: Any) -> None:
    with pytest.raises(Invalid):
        is_portable_data(value)


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
def test_is_portable_data__with_valid_value(value: Any) -> None:
    assert is_portable_data(value) == value
