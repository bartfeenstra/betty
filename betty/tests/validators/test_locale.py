from __future__ import annotations

from typing import Any

import pytest

from betty.locale import default_locale_tag, to_language_tag
from betty.validation import Invalid
from betty.validators.locale import is_locale


@pytest.mark.parametrize(
    "value",
    [
        default_locale_tag,
        "nl-NL",
        "uk",
    ],
)
def test_is_locale__with_valid_value(value: str) -> None:
    assert to_language_tag(is_locale(value)) == value


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        123,
        "",
        "non-existent-locale",
        object(),
        [],
        {},
    ],
)
def test_is_locale__with_invalid_value(value: Any) -> None:
    with pytest.raises(Invalid):
        is_locale(value)
