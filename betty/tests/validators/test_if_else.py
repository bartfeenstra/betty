from __future__ import annotations

import pytest

from betty.validation import InvalidGroup
from betty.validators.if_else import is_if_else
from betty.validators.int import NotAnInt, is_int
from betty.validators.str import NotAStr, is_str

_is_if_else = is_if_else(is_int, is_str)


def test_is_if_else__with_valid() -> None:
    assert _is_if_else(123) == 123
    assert _is_if_else("Hello, world!") == "Hello, world!"


def test_is_if_else__with_invalid() -> None:
    with pytest.raises(InvalidGroup) as exc_info:
        _is_if_else(True)
    assert isinstance(exc_info.value[0], NotAnInt)
    assert isinstance(exc_info.value[1], NotAStr)
