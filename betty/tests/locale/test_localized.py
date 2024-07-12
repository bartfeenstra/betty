from __future__ import annotations

from typing import Any

import pytest

from betty.locale.localized import Localized, negotiate_localizeds


class TestNegotiateLocalizeds:
    class DummyLocalized(Localized):
        def __eq__(self, other: Any) -> bool:
            if not isinstance(other, Localized):
                return NotImplemented
            return self.locale == other.locale

        def __repr__(self) -> str:
            return "%s(%s)" % (self.__class__.__name__, self.locale)

    @pytest.mark.parametrize(
        ("expected", "preferred_locale", "localizeds"),
        [
            (DummyLocalized(locale="nl"), "nl", [DummyLocalized(locale="nl")]),
            (DummyLocalized(locale="nl-NL"), "nl", [DummyLocalized(locale="nl-NL")]),
            (DummyLocalized(locale="nl"), "nl-NL", [DummyLocalized(locale="nl")]),
            (
                DummyLocalized(locale="nl-NL"),
                "nl-NL",
                [
                    DummyLocalized(locale="nl"),
                    DummyLocalized(locale="nl-BE"),
                    DummyLocalized(locale="nl-NL"),
                ],
            ),
            (
                DummyLocalized(locale="nl"),
                "nl",
                [DummyLocalized(locale="nl"), DummyLocalized(locale="en")],
            ),
            (
                DummyLocalized(locale="nl"),
                "nl",
                [DummyLocalized(locale="en"), DummyLocalized(locale="nl")],
            ),
            (DummyLocalized(locale="nl-NL"), "nl-BE", [DummyLocalized(locale="nl-NL")]),
            (None, "nl", []),
        ],
    )
    async def test_with_match_should_return_match(
        self,
        expected: Localized | None,
        preferred_locale: str,
        localizeds: list[Localized],
    ) -> None:
        assert expected == negotiate_localizeds(preferred_locale, localizeds)

    async def test_without_match_should_return_default(self) -> None:
        preferred_locale = "de"
        localizeds = [
            self.DummyLocalized(locale="nl"),
            self.DummyLocalized(locale="en"),
            self.DummyLocalized(locale="uk"),
        ]
        assert self.DummyLocalized(locale="nl") == negotiate_localizeds(
            preferred_locale, localizeds
        )
