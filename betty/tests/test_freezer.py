from typing import Any

import pytest

from betty.freezer import Frozen, is_frozen


@pytest.mark.parametrize(
    ("expected", "value"),
    [
        (True, Frozen()),
        (False, Frozen),
        (False, object()),
    ],
)
def test_is_frozen(expected: bool, value: Any) -> None:
    assert is_frozen(value) is expected
