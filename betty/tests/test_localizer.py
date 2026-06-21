from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

from babel import Locale

from betty.gettext import TranslationRepository
from betty.locale import default_locale, default_locale_tag
from betty.localizables.plain import Plain
from betty.localizer import Localizer, LocalizerRepository, default_localizer

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture

    from betty.localizable import (
        ShorthandStaticTranslations,
        StaticTranslationsMapping,
    )


class TestLocalizer:
    def test_locale(self) -> None:
        sut = default_localizer
        assert sut.locale.language == "en"

    def test_localize__with_localizable(self) -> None:
        localizable = "My First Localizable"
        assert default_localizer.localize(Plain(localizable)) == localizable

    def test_localize__with_str(self) -> None:
        localizable = "My First Localizable"
        assert default_localizer.localize(localizable) == localizable

    def test_localize__with_static_translations_mapping(self) -> None:
        locale = "nl"
        localizer = Localizer(locale, NullTranslations())
        localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
        localizable: StaticTranslationsMapping = {
            default_locale: "My First Localizable",
            Locale(locale): localized,
        }
        assert localizer.localize(localizable) == localized

    def test_localize__with_shorthand_static_translations_mapping(self) -> None:
        locale = "nl-NL"
        localizer = Localizer(locale, NullTranslations())
        localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
        localizable: ShorthandStaticTranslations = {
            default_locale_tag: "My First Localizable",
            locale: localized,
        }
        assert localizer.localize(localizable) == localized

    def test__(self) -> None:
        sut = default_localizer
        assert sut._("My First Translatable String") == "My First Translatable String"

    def test_gettext(self) -> None:
        sut = default_localizer
        assert (
            sut.gettext("My First Translatable String")
            == "My First Translatable String"
        )

    def test_ngettext__with_singular(self) -> None:
        sut = default_localizer
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 1
            )
            == "My First Translatable String"
        )

    def test_ngettext__with_plural(self) -> None:
        sut = default_localizer
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 9
            )
            == "My First Translatable Strings"
        )

    def test_npgettext__with_singular(self) -> None:
        sut = default_localizer
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
        sut = default_localizer
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
        sut = default_localizer
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
