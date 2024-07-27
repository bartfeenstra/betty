from gettext import NullTranslations

import pytest
from betty.locale.localizable import StaticTranslationsLocalizable
from betty.locale.localizable import (
    static,
    ShorthandStaticTranslations,
)
from betty.locale.localizer import Localizer


class TestStaticTranslationsLocalizable:
    async def test_without_translations(self) -> None:
        with pytest.raises(ValueError):  # noqa PT011
            StaticTranslationsLocalizable({})

    @pytest.mark.parametrize(
        ("expected", "locale", "translations"),
        [
            # A translation in an undetermined locale.
            (
                "Hello, world!",
                "en-US",
                "Hello, world!",
            ),
            # An exact locale match.
            (
                "Hello, world!",
                "en-US",
                {
                    "en-US": "Hello, world!",
                },
            ),
            # A negotiated locale match.
            (
                "Hello, world!",
                "en-US",
                {
                    "nl-NL": "Hallo, wereld!",
                    "en": "Hello, world!",
                },
            ),
            # No locale match, expect the fallback.
            (
                "Hello, world!",
                "de-DE",
                {
                    "en": "Hello, world!",
                    "nl-NL": "Hallo, wereld!",
                },
            ),
        ],
    )
    async def test_localize_with_translations(
        self, expected: str, locale: str, translations: ShorthandStaticTranslations
    ) -> None:
        sut = StaticTranslationsLocalizable(translations)
        localizer = Localizer(locale, NullTranslations())
        assert sut.localize(localizer) == expected


class TestStatic:
    @pytest.mark.parametrize(
        "translations",
        [
            "Hello, world!",
            {
                "en-US": "Hello, world!",
                "nl-NL": "Hallo, wereld!",
            },
        ],
    )
    async def test(self, translations: ShorthandStaticTranslations) -> None:
        static(translations)
