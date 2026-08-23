from __future__ import annotations

from typing import Any

import pytest

from betty.assertions.float import assert_float
from betty.exception import HumanFacingException


@pytest.mark.parametrize(
    ("value", "minimum", "maximum"),
    [
        (1.23, None, None),
        (1.23, 1.23, None),
        (1.23, None, 1.23),
    ],
)
def test_assert_float__with_valid_value(
    value: Any, minimum: float | None, maximum: float | None
) -> None:
    assert_float(minimum=minimum, maximum=maximum)(value)


@pytest.mark.parametrize(
    ("value", "minimum", "maximum"),
    [
        (123, None, None),
        (1.23, 1.24, None),
        (1.23, None, 1.22),
    ],
)
def test_assert_float__with_invalid_value(
    value: Any, minimum: float | None, maximum: float | None
) -> None:
    with pytest.raises(HumanFacingException):
        assert_float(minimum=minimum, maximum=maximum)(False)
