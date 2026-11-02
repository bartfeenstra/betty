from __future__ import annotations

from babel import Locale

from betty.localizables.static import StaticTranslations
from betty.localized import LocalizedStr
from betty.localizer import LocalizerRepository, default_localizer


class TestLocalizer:
    def test_locale(self) -> None:
        sut = default_localizer
        assert sut.locale.language == "en"

    def test_localize__with_localized_str(self) -> None:
        localizable = LocalizedStr("My First Localizable")
        assert default_localizer.localize(localizable) is localizable

    def test_localize__with_localizable(self) -> None:
        localizable = "My First Localizable"
        assert (
            default_localizer.localize(StaticTranslations(localizable)) == localizable
        )

    def test_localize__with_str(self) -> None:
        localizable = "My First Localizable"
        assert default_localizer.localize(localizable) == localizable


class TestLocalizerRepository:
    async def test_get(self) -> None:
        locale = "nl"
        sut = LocalizerRepository()
        localizer = await sut.get(locale)
        assert localizer.locale == Locale(locale)
        assert await sut.get(locale) is localizer
