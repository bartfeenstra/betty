from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

from babel import Locale

from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable.plain import Plain
from betty.locale.localize import (
    DEFAULT_LOCALIZER,
    Localizer,
    LocalizerRepository,
    resolve_localized,
)
from betty.locale.translation import TranslationRepository

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture

    from betty.locale.localizable import (
        ShorthandStaticTranslations,
        StaticTranslationsMapping,
    )


class TestLocalizer:
    def test_locale(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.locale.language == "en"

    def test__(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut._("My First Translatable String") == "My First Translatable String"

    def test_gettext(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.gettext("My First Translatable String")
            == "My First Translatable String"
        )

    def test_ngettext__with_singular(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 1
            )
            == "My First Translatable String"
        )

    def test_ngettext__with_plural(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 9
            )
            == "My First Translatable Strings"
        )

    def test_npgettext__with_singular(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.npgettext(
                "My First Context",
                "My First Translatable String",
                "My First Translatable Strings",
                1,
            )
            == "My First Translatable String"
        )

    def test_npgettext__with_plural(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.npgettext(
                "My First Context",
                "My First Translatable String",
                "My First Translatable Strings",
                9,
            )
            == "My First Translatable Strings"
        )

    def test_pgettext(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.pgettext("My First Context", "My First Translatable String")
            == "My First Translatable String"
        )


class TestLocalizerRepository:
    def test_get(self, mocker: MockerFixture, tmp_path: Path) -> None:
        locale = "nl"
        m_translations = mocker.MagicMock(spec=TranslationRepository)
        sut = LocalizerRepository(m_translations)
        localizer = sut.get(locale)
        assert localizer.locale == Locale(locale)
        assert sut.get(locale) is localizer


def test_resolve_localized__with_localizable() -> None:
    localizable = "My First Localizable"
    assert (
        resolve_localized(Plain(localizable), localizer=DEFAULT_LOCALIZER)
        == localizable
    )


def test_resolve_localized__with_str() -> None:
    localizable = "My First Localizable"
    assert resolve_localized(localizable, localizer=DEFAULT_LOCALIZER) == localizable


def test_resolve_localized__with_static_translations_mapping() -> None:
    locale = "nl"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        Locale(locale): localized,
    }
    assert resolve_localized(localizable, localizer=localizer) == localized


def test_resolve_localized__with_shorthand_static_translations_mapping() -> None:
    locale = "nl-NL"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: ShorthandStaticTranslations = {
        DEFAULT_LOCALE_TAG: "My First Localizable",
        locale: localized,
    }  # ty:ignore[invalid-assignment]
    assert resolve_localized(localizable, localizer=localizer) == localized
