from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.assertions.number import assert_number
from betty.exception import HumanFacingException

if TYPE_CHECKING:
    from betty.typing import Number


@pytest.mark.parametrize(
    ("value", "minimum", "maximum"),
    [
        (123, None, None),
        (123, 123, None),
        (123, None, 123),
    ],
)
def test_assert_number__with_valid_value(
    value: Any, minimum: Number | None, maximum: Number | None
) -> None:
    assert_number(minimum=minimum, maximum=maximum)(value)


@pytest.mark.parametrize(
    ("value", "minimum", "maximum"),
    [
        (object(), None, None),
        (123, 124, None),
        (1.23, 1.24, None),
        (123, None, 122),
        (1.23, None, 1.22),
    ],
)
def test_assert_number__with_invalid_value(
    value: Any, minimum: Number | None, maximum: Number | None
) -> None:
    with pytest.raises(HumanFacingException):
        assert_number(minimum=minimum, maximum=maximum)(False)
