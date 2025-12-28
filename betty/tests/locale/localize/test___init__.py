from __future__ import annotations

from typing import TYPE_CHECKING

from babel import Locale

from betty.locale.localize import DEFAULT_LOCALIZER, LocalizerRepository
from betty.locale.translation import TranslationRepository

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


class TestLocalizer:
    async def test_locale(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut.locale.language == "en"

    async def test__(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert sut._("My First Translatable String") == "My First Translatable String"

    async def test_gettext(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.gettext("My First Translatable String")
            == "My First Translatable String"
        )

    async def test_ngettext__with_singular(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 1
            )
            == "My First Translatable String"
        )

    async def test_ngettext__with_plural(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.ngettext(
                "My First Translatable String", "My First Translatable Strings", 9
            )
            == "My First Translatable Strings"
        )

    async def test_npgettext__with_singular(self) -> None:
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

    async def test_npgettext__with_plural(self) -> None:
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

    async def test_pgettext(self) -> None:
        sut = DEFAULT_LOCALIZER
        assert (
            sut.pgettext("My First Context", "My First Translatable String")
            == "My First Translatable String"
        )


class TestLocalizerRepository:
    async def test_get(self, mocker: MockerFixture, tmp_path: Path) -> None:
        locale = "nl"
        m_translations = mocker.MagicMock(spec=TranslationRepository)
        sut = LocalizerRepository(m_translations)
        localizer = sut.get(locale)
        assert localizer.locale == Locale(locale)
        assert sut.get(locale) is localizer
