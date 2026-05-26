from __future__ import annotations

from typing import Any

import pytest

from betty.assertions.locale import assert_locale
from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE_TAG, to_language_tag


@pytest.mark.parametrize(
    "value",
    [
        DEFAULT_LOCALE_TAG,
        "nl-NL",
        "uk",
    ],
)
def test_assert_locale__with_valid_value(value: str) -> None:
    assert to_language_tag(assert_locale()(value)) == value


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
def test_assert_locale__with_invalid_value(value: Any) -> None:
    with pytest.raises(HumanFacingException):
        assert_locale()(value)
