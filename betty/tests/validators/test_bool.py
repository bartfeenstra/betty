from __future__ import annotations

import pytest

from betty.validators.bool import NotABool, is_bool


def test_is_bool__with_valid_value() -> None:
    assert is_bool(True) is True
    assert is_bool(False) is False


def test_is_bool__with_invalid_value() -> None:
    with pytest.raises(NotABool):
        is_bool(123)
