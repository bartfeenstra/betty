from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

import pytest
from babel import Locale

from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable import (
    Plain,
    ShorthandStaticTranslations,
    StaticTranslationsMapping,
)
from betty.locale.localized import (
    Localized,
    LocalizedStr,
    ensure_localized,
    negotiate_localizeds,
)
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.test_utils.locale.localized import DummyLocalized

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestLocalized:
    def test_locale(self) -> None:
        locale = Locale("nl")
        sut = DummyLocalized(locale)
        assert sut.locale is locale


class TestLocalizedStr:
    def test_with_locale(self) -> None:
        string = "Hallo, wereld!"
        locale = Locale("nl")
        sut = LocalizedStr(string, locale=locale)
        assert sut == string
        assert sut.locale is locale


@pytest.mark.parametrize(
    ("expected", "preferred_locale", "localizeds"),
    [
        (Locale("nl"), Locale("nl"), [DummyLocalized("nl")]),
        (Locale("nl", "NL"), Locale("nl"), [DummyLocalized("nl-NL")]),
        (Locale("nl"), Locale("nl", "NL"), [DummyLocalized("nl")]),
        (
            Locale("nl", "NL"),
            Locale("nl", "NL"),
            [
                DummyLocalized("nl"),
                DummyLocalized("nl-BE"),
                DummyLocalized("nl-NL"),
            ],
        ),
        (
            Locale("nl"),
            Locale("nl"),
            [DummyLocalized("nl"), DummyLocalized("en")],
        ),
        (
            Locale("nl"),
            Locale("nl"),
            [DummyLocalized("en"), DummyLocalized("nl")],
        ),
        (Locale("nl", "NL"), Locale("nl", "BE"), [DummyLocalized("nl-NL")]),
        (None, Locale("nl"), []),
    ],
)
async def test_negotiate_localizeds__with_match_should_return_match(
    expected: Locale | None,
    preferred_locale: Locale,
    localizeds: Sequence[Localized],
) -> None:
    actual = negotiate_localizeds(preferred_locale, localizeds)
    if expected is None:
        assert actual is None
    else:
        assert actual is not None
        assert actual.locale == expected


async def test_negotiate_localizeds__without_match_should_return_default() -> None:
    localizeds = [
        DummyLocalized("nl"),
        DummyLocalized("en"),
        DummyLocalized("uk"),
    ]
    actual = negotiate_localizeds(Locale("de"), localizeds)
    assert actual is not None
    assert actual.locale == Locale("nl")


def test_ensure_localized__with_localizable() -> None:
    localizable = "My First Localizable"
    assert (
        ensure_localized(Plain(localizable), localizer=DEFAULT_LOCALIZER) == localizable
    )


def test_ensure_localized__with_str() -> None:
    localizable = "My First Localizable"
    assert ensure_localized(localizable, localizer=DEFAULT_LOCALIZER) == localizable


def test_ensure_localized__with_static_translations_mapping() -> None:
    locale = "nl"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        Locale(locale): localized,
    }
    assert ensure_localized(localizable, localizer=localizer) == localized


def test_ensure_localized__with_shorthand_static_translations_mapping() -> None:
    locale = "nl-NL"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: ShorthandStaticTranslations = {
        DEFAULT_LOCALE_TAG: "My First Localizable",
        locale: localized,
    }
    assert ensure_localized(localizable, localizer=localizer) == localized
