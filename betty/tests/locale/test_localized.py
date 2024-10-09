from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.locale.localized import Localized, negotiate_localizeds, LocalizedStr
from betty.test_utils.locale.localized import DummyLocalized

if TYPE_CHECKING:
    from collections.abc import Sequence


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
            ("nl", "nl", [DummyLocalized("nl")]),
            ("nl-NL", "nl", [DummyLocalized("nl-NL")]),
            ("nl", "nl-NL", [DummyLocalized("nl")]),
            (
                "nl-NL",
                "nl-NL",
                [
                    DummyLocalized("nl"),
                    DummyLocalized("nl-BE"),
                    DummyLocalized("nl-NL"),
                ],
            ),
            (
                "nl",
                "nl",
                [DummyLocalized("nl"), DummyLocalized("en")],
            ),
            (
                "nl",
                "nl",
                [DummyLocalized("en"), DummyLocalized("nl")],
            ),
            ("nl-NL", "nl-BE", [DummyLocalized("nl-NL")]),
            (None, "nl", []),
        ],
    )
    async def test_with_match_should_return_match(
        self,
        expected: str | None,
        preferred_locale: str,
        localizeds: Sequence[Localized],
    ) -> None:
        actual = negotiate_localizeds(preferred_locale, localizeds)
        if expected is None:
            assert actual is None
        else:
            assert actual is not None
            assert actual.locale == expected

    async def test_without_match_should_return_default(self) -> None:
        preferred_locale = "de"
        localizeds = [
            DummyLocalized("nl"),
            DummyLocalized("en"),
            DummyLocalized("uk"),
        ]
        actual = negotiate_localizeds(preferred_locale, localizeds)
        assert actual is not None
        assert actual.locale == "nl"
