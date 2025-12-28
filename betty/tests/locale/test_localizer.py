from __future__ import annotations

import gettext
from typing import TYPE_CHECKING

from babel import Locale

from betty.locale.localizer import Localizer, LocalizerRepository
from betty.locale.translation import TranslationRepository

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


class TestLocalizer:
    async def test_locale(self) -> None:
        locale = Locale("nl")
        sut = Localizer(locale, gettext.NullTranslations())
        assert sut.locale is locale

    async def test_translations(self) -> None:
        translations = gettext.NullTranslations()
        sut = Localizer(Locale("nl"), translations)
        assert sut.translations is translations


class TestLocalizerRepository:
    async def test_get(self, mocker: MockerFixture, tmp_path: Path) -> None:
        locale = "nl"
        m_translations = mocker.MagicMock(spec=TranslationRepository)
        sut = LocalizerRepository(m_translations)
        localizer = sut.get(locale)
        assert localizer.locale == Locale(locale)
        assert sut.get(locale) is localizer
