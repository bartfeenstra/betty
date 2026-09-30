from __future__ import annotations

import pytest

from betty.validation import Invalid
from betty.validators.bool import is_bool


def test_is_bool__with_valid_value() -> None:
    is_bool(True)


def test_is_bool__with_invalid_value() -> None:
    with pytest.RaisesGroup(Invalid):
        is_bool(123)
