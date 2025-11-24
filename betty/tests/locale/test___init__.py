from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import pytest

from betty.locale import (
    MULTIPLE_LOCALES,
    NO_LINGUISTIC_CONTENT,
    SPECIAL_LOCALES,
    LocaleLike,
    merge_locales,
    negotiate_locale,
    to_locale,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


@pytest.mark.parametrize(
    ("expected", "locales"),
    [
        # No locales.
        (NO_LINGUISTIC_CONTENT, []),
        # A single locale which is passed through.
        ("nl", ["nl"]),
        ("de-DE", ["de-DE"]),
        *((locale, [locale]) for locale in SPECIAL_LOCALES),
        # Multiple locales.
        (MULTIPLE_LOCALES, ["nl", "de-DE"]),
        # Multiple locales, including no linguistic content.
        ("nl", ["nl", NO_LINGUISTIC_CONTENT]),
        (MULTIPLE_LOCALES, ["nl", "de-DE", NO_LINGUISTIC_CONTENT]),
        *(
            (locale, [locale, NO_LINGUISTIC_CONTENT])
            for locale in SPECIAL_LOCALES
            if locale is not NO_LINGUISTIC_CONTENT
        ),
    ],
)
def test_merge_locales(expected: str, locales: Sequence[str]) -> None:
    assert merge_locales(*locales) == expected


@pytest.mark.parametrize(
    ("expected", "preferred_locale", "available_locales"),
    [
        ("nl", "nl", ["nl"]),
        ("nl-NL", "nl", ["nl-NL"]),
        ("nl", "nl-NL", ["nl"]),
        ("nl-NL", "nl-NL", ["nl", "nl-BE", "nl-NL"]),
        ("nl", "nl", ["nl", "en"]),
        ("nl", "nl", ["en", "nl"]),
        ("nl-NL", "nl-BE", ["nl-NL"]),
    ],
)
async def test_negotiate_locale(
    expected: LocaleLike | None,
    preferred_locale: LocaleLike,
    available_locales: Sequence[LocaleLike],
) -> None:
    actual = negotiate_locale(preferred_locale, available_locales)
    assert expected == (to_locale(actual) if actual else actual)
