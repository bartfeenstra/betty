from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pytest

from betty.locale.localized import Localized, negotiate_localizeds, LocalizedStr

if TYPE_CHECKING:
    from collections.abc import Sequence


class DummyLocalized(Localized):
    def __init__(self, locale: str):
        self._locale = locale

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Localized):
            return NotImplemented
        return self.locale == other.locale

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.locale})"


class TestLocalized:
    def test_locale(self) -> None:
        locale = "nl"
        sut = DummyLocalized(locale)
        assert sut.locale == locale


class TestLocalizedStr:
    def test_with_locale(self) -> None:
        string = "Hallo, wereld!"
        locale = "nl"
        sut = LocalizedStr(string, locale=locale)
        assert sut == string
        assert sut.locale == locale


class TestNegotiateLocalizeds:
    @pytest.mark.parametrize(
        ("expected", "preferred_locale", "localizeds"),
        [
            (DummyLocalized("nl"), "nl", [DummyLocalized("nl")]),
            (DummyLocalized("nl-NL"), "nl", [DummyLocalized("nl-NL")]),
            (DummyLocalized("nl"), "nl-NL", [DummyLocalized("nl")]),
            (
                DummyLocalized("nl-NL"),
                "nl-NL",
                [
                    DummyLocalized("nl"),
                    DummyLocalized("nl-BE"),
                    DummyLocalized("nl-NL"),
                ],
            ),
            (
                DummyLocalized("nl"),
                "nl",
                [DummyLocalized("nl"), DummyLocalized("en")],
            ),
            (
                DummyLocalized("nl"),
                "nl",
                [DummyLocalized("en"), DummyLocalized("nl")],
            ),
            (DummyLocalized("nl-NL"), "nl-BE", [DummyLocalized("nl-NL")]),
            (None, "nl", []),
        ],
    )
    async def test_with_match_should_return_match(
        self,
        expected: Localized | None,
        preferred_locale: str,
        localizeds: Sequence[Localized],
    ) -> None:
        assert expected == negotiate_localizeds(preferred_locale, localizeds)

    async def test_without_match_should_return_default(self) -> None:
        preferred_locale = "de"
        localizeds = [
            DummyLocalized("nl"),
            DummyLocalized("en"),
            DummyLocalized("uk"),
        ]
        assert DummyLocalized("nl") == negotiate_localizeds(
            preferred_locale, localizeds
        )
