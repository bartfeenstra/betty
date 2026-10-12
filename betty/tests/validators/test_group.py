from __future__ import annotations

import pytest

from betty.validation import InvalidGroup
from betty.validators.group import is_any
from betty.validators.int import NotAnInt, is_int
from betty.validators.str import NotAStr, is_str

_is_any = is_any(is_int, is_str)


def test_is_any__with_valid() -> None:
    assert _is_any(123) == 123
    assert _is_any("Hello, world!") == "Hello, world!"


def test_is_any__with_invalid() -> None:
    with pytest.raises(InvalidGroup) as exc_info:
        _is_any(True)
    assert isinstance(exc_info.value[0], NotAnInt)
    assert isinstance(exc_info.value[1], NotAStr)
