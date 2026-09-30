from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.localizables.static import StaticTranslations
from betty.validation import Invalid
from betty.validators.if_else import is_if_else

if TYPE_CHECKING:
    from betty.validation import Validator


def _always_valid(value: int) -> int:
    return value


def _always_invalid(value: int) -> int:
    raise Invalid(StaticTranslations(""))


@pytest.mark.parametrize(
    ("is_if", "is_else", "value"),
    [
        (_always_valid, _always_valid, 123),
        (_always_valid, _always_invalid, 123),
        (_always_invalid, _always_valid, 123),
    ],
)
def test_is_if_else__with_valid_validator(
    is_if: Validator[Any, bool], is_else: Validator[Any, bool], value: int
) -> None:
    assert is_if_else(is_if, is_else)(value) == value


def test_is_if_else__with_invalid_validator() -> None:
    with pytest.RaisesGroup(Invalid):
        is_if_else(_always_invalid, _always_invalid)(123)
