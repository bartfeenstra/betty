from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.assertions.int import assert_int
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
def test_assert_int__with_valid_value(
    value: Any, minimum: Number | None, maximum: Number | None
) -> None:
    assert_int(minimum=minimum, maximum=maximum)(value)


@pytest.mark.parametrize(
    ("value", "minimum", "maximum"),
    [
        (1.23, None, None),
        (123, 124, None),
        (123, None, 122),
    ],
)
def test_assert_int__with_invalid_value(
    value: Any, minimum: Number | None, maximum: Number | None
) -> None:
    with pytest.raises(HumanFacingException):
        assert_int(minimum=minimum, maximum=maximum)(False)
