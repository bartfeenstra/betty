from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import pytest
from babel import Locale

from betty.locale import (
    LocaleLike,
    ensure_locale,
    from_language_tag,
    negotiate_locale,
    to_language_tag,
)
from betty.locale.error import InvalidLocale, UnknownLocale

if TYPE_CHECKING:
    from collections.abc import Sequence


@pytest.mark.parametrize(
    ("expected", "preferred_locale", "available_locales"),
    [
        (
            Locale("nl"),
            Locale("nl"),
            [Locale("nl")],
        ),
        (
            Locale("nl", "NL"),
            Locale("nl"),
            [Locale("nl", "NL")],
        ),
        (
            Locale("nl"),
            Locale("nl", "NL"),
            [Locale("nl")],
        ),
        (
            Locale("nl", "NL"),
            Locale("nl", "NL"),
            [Locale("nl"), Locale("nl", "BE"), Locale("nl", "NL")],
        ),
        (
            Locale("nl"),
            Locale("nl"),
            [Locale("nl"), Locale("en")],
        ),
        (
            Locale("nl"),
            Locale("nl"),
            [Locale("en"), Locale("nl")],
        ),
        (
            Locale("nl", "NL"),
            Locale("nl", "BE"),
            [Locale("nl", "NL")],
        ),
    ],
)
async def test_negotiate_locale(
    expected: Locale | None,
    preferred_locale: Locale,
    available_locales: Sequence[Locale],
) -> None:
    assert negotiate_locale(preferred_locale, available_locales) == expected


@pytest.mark.parametrize(
    ("expected", "locale"),
    [
        (Locale("nl"), "nl"),
        (Locale("nl", "NL"), "nl-NL"),
        (Locale("nl"), Locale("nl")),
    ],
)
def test_ensure_locale(expected: Locale, locale: LocaleLike) -> None:
    assert ensure_locale(locale) == expected


@pytest.mark.parametrize(
    ("expected", "locale"),
    [
        (Locale("nl"), "nl"),
        (Locale("nl", "NL"), "nl-NL"),
    ],
)
def test_from_language_tag(expected: Locale, locale: str) -> None:
    assert from_language_tag(locale) == expected


@pytest.mark.parametrize(
    "locale",
    [
        "",
        "nl_NL",
        "nl--NL",
    ],
)
def test_from_language_tag__with_invalid_locale(locale: str) -> None:
    with pytest.raises(InvalidLocale):
        from_language_tag(locale)


def test_from_language_tag__with_unknown_locale() -> None:
    with pytest.raises(UnknownLocale):
        from_language_tag("myfirstlocale")


@pytest.mark.parametrize(
    ("expected", "locale"),
    [
        ("und", None),
        ("nl", Locale("nl")),
        ("nl-NL", Locale("nl", "NL")),
    ],
)
def test_to_language_tag(expected: str, locale: Locale | None) -> None:
    assert to_language_tag(locale) == expected
