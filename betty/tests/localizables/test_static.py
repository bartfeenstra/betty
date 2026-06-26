from gettext import NullTranslations

import pytest
from babel import Locale

from betty.exception import HumanFacingException
from betty.locale import default_locale, default_locale_tag, resolve_locale
from betty.locale.error import UnknownLocale
from betty.localizable import (
    LocalizableCount,
    ShorthandCountableStaticTranslations,
    ShorthandStaticTranslations,
    StaticTranslationsMapping,
)
from betty.localizables.static import (
    CountableStaticTranslations,
    InvalidPluralTag,
    MissingPluralPlaceholder,
    MissingPluralTag,
    StaticTranslations,
)
from betty.localizer import Localizer, default_localizer


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
    def test_localize__with_translations(
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
    def test_translations(
        self,
        expected: StaticTranslationsMapping,
        translations: ShorthandStaticTranslations,
    ) -> None:
        sut = StaticTranslations(translations)
        assert sut.translations == expected

    def test_load__without_translations_should_error(self) -> None:
        with pytest.raises(HumanFacingException):
            StaticTranslations.load({})

    def test_load__with_single_undetermined_translation(self) -> None:
        localizable = "Hello, world!"
        assert (
            StaticTranslations.load(localizable).localize(default_localizer)
            == localizable
        )

    def test_dump__with_static_translations_single_undetermined(self) -> None:
        localizable = "Hello, world!"
        assert StaticTranslations(localizable).dump() == localizable

    def test_dump_localizable__with_static_translations(self) -> None:
        localizable: ShorthandStaticTranslations = {
            default_locale_tag: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }

        assert StaticTranslations(localizable).dump() == localizable


class TestCountableStaticTranslations:
    def test___init____with_missing_placeholder(self) -> None:
        with pytest.raises(MissingPluralPlaceholder):
            CountableStaticTranslations({
                "en-US": {
                    "one": "hello, world!",
                    "other": "hello, worlds!",
                },
            })

    def test___init____with_invalid_plural_tag(self) -> None:
        invalid_plural_tag = "invalid-tag"

        with pytest.raises(InvalidPluralTag) as exc_info:
            CountableStaticTranslations({
                "en-US": {
                    invalid_plural_tag: "{count}",
                    "one": "{count} hello, world!",
                    "other": "{count} hello, worlds!",
                },
            })
        assert invalid_plural_tag in str(exc_info.value)

    def test___init____with_missing_plural_tag(self) -> None:
        with pytest.raises(MissingPluralTag) as exc_info:
            CountableStaticTranslations({
                "en-US": {
                    "one": "{count} hello, world!",
                },
            })
        assert "other" in str(exc_info.value)

    def test_translations(self) -> None:
        sut = CountableStaticTranslations({
            default_locale_tag: {
                "one": "{count} hello, world!",
                "other": "{count} hello, worlds!",
            },
        })
        assert sut.translations == {
            default_locale: {
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
    def test_count(
        self,
        expected: str,
        count: LocalizableCount,
        locale: str,
        translations: ShorthandCountableStaticTranslations,
    ) -> None:
        sut = CountableStaticTranslations(translations)
        assert (
            sut.count(count).localize(
                Localizer(resolve_locale(locale), NullTranslations())
            )
            == expected
        )

    def test_load(self) -> None:
        loaded = CountableStaticTranslations.load({
            default_locale_tag: {
                "one": "{count} thing",
                "other": "{count} things",
            },
        })
        assert loaded.count(1).localize(default_localizer) == "1 thing"

    def test_load__without_locales(self) -> None:
        with pytest.raises(HumanFacingException):
            CountableStaticTranslations.load({})

    def test_load__with_unknown_locale(self) -> None:
        with pytest.raises(UnknownLocale):
            CountableStaticTranslations.load({
                "unknownlocale": {},
            })

    def test_load__with_missing_plural_tag(self) -> None:
        with pytest.raises(MissingPluralTag):
            CountableStaticTranslations.load({
                default_locale_tag: {},
            })

    def test_load__with_invalid_plural_tag(self) -> None:
        with pytest.raises(InvalidPluralTag):
            CountableStaticTranslations.load({
                default_locale_tag: {
                    "one": "{count}",
                    "other": "{count}",
                    "invalid": "{count}",
                },
            })

    def test_dump(self) -> None:
        assert CountableStaticTranslations({
            default_locale_tag: {
                "one": "{count} thing",
                "other": "{count} things",
            }
        }).dump() == {
            default_locale_tag: {
                "one": "{count} thing",
                "other": "{count} things",
            }
        }
