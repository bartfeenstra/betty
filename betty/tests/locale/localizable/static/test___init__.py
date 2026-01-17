from gettext import NullTranslations

import pytest
from babel import Locale

from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, ensure_locale
from betty.locale.localizable import (
    LocalizableCount,
    ShorthandCountableStaticTranslations,
    ShorthandStaticTranslations,
    StaticTranslationsMapping,
)
from betty.locale.localizable.error import (
    InvalidPluralTag,
    MissingPluralPlaceholder,
    MissingPluralTag,
)
from betty.locale.localizable.static import (
    CountableStaticTranslations,
    StaticTranslations,
)
from betty.locale.localize import Localizer


class TestStaticTranslations:
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
    async def test_localize__with_translations(
        self, expected: str, locale: str, translations: ShorthandStaticTranslations
    ) -> None:
        sut = StaticTranslations(translations)
        localizer = Localizer(locale, NullTranslations())
        assert sut.localize(localizer) == expected

    @pytest.mark.parametrize(
        ("expected", "translations"),
        [
            (
                {None: "Hello, world!"},
                "Hello, world!",
            ),
            (
                {
                    Locale("en", "US"): "Hello, world!",
                },
                {
                    "en-US": "Hello, world!",
                },
            ),
            (
                {
                    Locale("nl", "NL"): "Hallo, wereld!",
                    Locale("en"): "Hello, world!",
                },
                {
                    "nl-NL": "Hallo, wereld!",
                    "en": "Hello, world!",
                },
            ),
        ],
    )
    async def test_translations(
        self,
        expected: StaticTranslationsMapping,
        translations: ShorthandStaticTranslations,
    ) -> None:
        sut = StaticTranslations(translations)
        assert sut.translations == expected


class TestCountableStaticTranslations:
    async def test___init____with_missing_placeholder(self) -> None:
        with pytest.raises(MissingPluralPlaceholder):
            CountableStaticTranslations(
                {
                    "en-US": {
                        "one": "hello, world!",
                        "other": "hello, worlds!",
                    },
                }
            )

    async def test___init____with_invalid_plural_tag(self) -> None:
        invalid_plural_tag = "invalid-tag"

        with pytest.raises(InvalidPluralTag) as exc_info:
            CountableStaticTranslations(
                {
                    "en-US": {
                        invalid_plural_tag: "{count}",
                        "one": "{count} hello, world!",
                        "other": "{count} hello, worlds!",
                    },
                }
            )
        assert invalid_plural_tag in str(exc_info.value)

    async def test___init____with_missing_plural_tag(self) -> None:
        with pytest.raises(MissingPluralTag) as exc_info:
            CountableStaticTranslations(
                {
                    "en-US": {
                        "one": "{count} hello, world!",
                    },
                }
            )
        assert "other" in str(exc_info.value)

    async def test_translations(self) -> None:
        sut = CountableStaticTranslations(
            {
                DEFAULT_LOCALE_TAG: {
                    "one": "{count} hello, world!",
                    "other": "{count} hello, worlds!",
                },
            }
        )
        assert sut.translations == {
            DEFAULT_LOCALE: {
                "one": "{count} hello, world!",
                "other": "{count} hello, worlds!",
            },
        }

    @pytest.mark.parametrize(
        ("expected", "count", "locale", "translations"),
        [
            (
                "1 hello, world!",
                1,
                "en-US",
                {
                    "en-US": {
                        "one": "{count} hello, world!",
                        "other": "{count} hello, worlds!",
                    },
                },
            ),
            (
                "2 hello, worlds!",
                2,
                "en-US",
                {
                    "en-US": {
                        "one": "{count} hello, world!",
                        "other": "{count} hello, worlds!",
                    },
                },
            ),
        ],
    )
    async def test_count(
        self,
        expected: str,
        count: LocalizableCount,
        locale: str,
        translations: ShorthandCountableStaticTranslations,
    ) -> None:
        sut = CountableStaticTranslations(translations)
        assert (
            sut.count(count).localize(
                Localizer(ensure_locale(locale), NullTranslations())
            )
            == expected
        )
