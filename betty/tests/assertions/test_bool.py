from __future__ import annotations

import pytest

from betty.assertions.bool import assert_bool
from betty.exception import HumanFacingException


def test_assert_bool__with_valid_value() -> None:
    assert_bool(True)


def test_assert_bool__with_invalid_value() -> None:
    with pytest.raises(HumanFacingException):
        assert_bool(123)
