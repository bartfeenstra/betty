from __future__ import annotations

from typing import TYPE_CHECKING

from babel import Locale

from betty.locale import default_locale, default_locale_tag
from betty.localizables.plain import Plain
from betty.localizer import Localizer, LocalizerRepository, default_localizer

if TYPE_CHECKING:
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
        localizer = Localizer(locale)
        localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
        localizable: StaticTranslationsMapping = {
            default_locale: "My First Localizable",
            Locale(locale): localized,
        }
        assert localizer.localize(localizable) == localized

    def test_localize__with_shorthand_static_translations_mapping(self) -> None:
        locale = "nl-NL"
        localizer = Localizer(locale)
        localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
        localizable: ShorthandStaticTranslations = {
            default_locale_tag: "My First Localizable",
            locale: localized,
        }
        assert localizer.localize(localizable) == localized


class TestLocalizerRepository:
    async def test_get(self) -> None:
        locale = "nl"
        sut = LocalizerRepository()
        localizer = await sut.get(locale)
        assert localizer.locale == Locale(locale)
        assert await sut.get(locale) is localizer
