from collections.abc import Sequence
from gettext import NullTranslations

import pytest
from babel import Locale
from typing_extensions import override

from betty.attr import AttrNotInitialized
from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, ensure_locale
from betty.locale.localizable import (
    AllEnumeration,
    AnyEnumeration,
    Chain,
    CountableLocalizable,
    CountableStaticTranslations,
    Lines,
    Localizable,
    LocalizableCount,
    LocalizableLike,
    OptionalLocalizableAttr,
    OrderedList,
    Paragraph,
    Paragraphs,
    Plain,
    RequiredCountableLocalizableAttr,
    RequiredLocalizableAttr,
    ShorthandCountableStaticTranslations,
    ShorthandStaticTranslations,
    StaticTranslations,
    StaticTranslationsMapping,
    UnorderedList,
    do_you_mean,
    ensure_countable_localizable,
    ensure_localizable,
)
from betty.locale.localizable.error import (
    InvalidPluralTag,
    MissingPluralPlaceholder,
    MissingPluralTag,
)
from betty.locale.localized import ensure_localized
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.test_utils.exception import assert_error


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
        with pytest.raises(HumanFacingException) as exc_info:
            CountableStaticTranslations(
                {
                    "en-US": {
                        "one": "hello, world!",
                        "other": "hello, worlds!",
                    },
                }
            )
        assert_error(exc_info.value, error_type=MissingPluralPlaceholder)

    async def test___init____with_invalid_plural_tag(self) -> None:
        invalid_plural_tag = "invalid-tag"

        with pytest.raises(HumanFacingException) as exc_info:
            CountableStaticTranslations(
                {
                    "en-US": {
                        invalid_plural_tag: "???",
                        "one": "{count} hello, world!",
                        "other": "{count} hello, worlds!",
                    },
                }
            )
        for error in assert_error(exc_info.value, error_type=InvalidPluralTag):
            assert invalid_plural_tag in str(error)

    async def test___init____with_missing_plural_tag(self) -> None:
        with pytest.raises(HumanFacingException) as exc_info:
            CountableStaticTranslations(
                {
                    "en-US": {
                        "one": "{count} hello, world!",
                    },
                }
            )
        for error in assert_error(exc_info.value, error_type=MissingPluralTag):
            assert "other" in str(error)

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


class TestPlain:
    def test_text(self) -> None:
        text = "Hello, world!"
        assert Plain(text).text == text

    def test_locale(self) -> None:
        locale = Locale("nl")
        assert Plain("-", locale).locale is locale

    @pytest.mark.parametrize(
        "string",
        [
            "Hello, world!",
            "Hallo, wereld!",
        ],
    )
    def test_localize(self, string: str) -> None:
        assert Plain(string).localize(DEFAULT_LOCALIZER) == string


@pytest.mark.parametrize(
    ("expected", "available_options"),
    [
        ("There are no available options.", []),
        ("Do you mean foo?", ["foo"]),
        ("Do you mean one of bar, baz, or foo?", ["foo", "bar", "baz"]),
    ],
)
async def test_do_you_mean(expected: str, available_options: Sequence[str]) -> None:
    assert do_you_mean(*available_options).localize(DEFAULT_LOCALIZER) == expected


class TestCountableLocalizable:
    class _Sut(CountableLocalizable):
        @override
        def count(self, count: LocalizableCount, /) -> Localizable:
            return Plain("{format_placeholder}")

    def test_format(self) -> None:
        sut = self._Sut()
        assert (
            sut.count(9)
            .format(format_placeholder="format-value")
            .localize(DEFAULT_LOCALIZER)
            == "format-value"
        )


class TestLines:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo\nBar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test_localize(
        self, expected: str, localizables: Sequence[LocalizableLike]
    ) -> None:
        sut = Lines(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestParagraph:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo Bar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test_localize(
        self, expected: str, localizables: Sequence[LocalizableLike]
    ) -> None:
        sut = Paragraph(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestParagraphs:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo\n\nBar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test_localize(
        self, expected: str, localizables: Sequence[LocalizableLike]
    ) -> None:
        sut = Paragraphs(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestOrderedList:
    @pytest.mark.parametrize(
        ("expected", "localizer", "localizables"),
        [
            (
                "",
                DEFAULT_LOCALIZER,
                [],
            ),
            (
                "1. Foo\n2. Bar",
                DEFAULT_LOCALIZER,
                ["Foo", "Bar"],
            ),
            (
                "Foo .1\nBar .2",
                Localizer("ar", NullTranslations()),
                ["Foo", "Bar"],
            ),
            (
                "1. Foo\n   Foo2\n2. Bar\n   Bar2",
                DEFAULT_LOCALIZER,
                [Plain("Foo\nFoo2"), Plain("Bar\nBar2")],
            ),
            (
                "1.  1\n2.  2\n3.  3\n4.  4\n5.  5\n6.  6\n7.  7\n8.  8\n9.  9\n10. 10",
                DEFAULT_LOCALIZER,
                [
                    Plain("1"),
                    Plain("2"),
                    Plain("3"),
                    Plain("4"),
                    Plain("5"),
                    Plain("6"),
                    Plain("7"),
                    Plain("8"),
                    Plain("9"),
                    Plain("10"),
                ],
            ),
        ],
    )
    def test_localize(
        self,
        expected: str,
        localizer: Localizer,
        localizables: Sequence[LocalizableLike],
    ) -> None:
        sut = OrderedList(*localizables)
        assert sut.localize(localizer) == expected


class TestUnorderedList:
    @pytest.mark.parametrize(
        ("expected", "localizer", "localizables"),
        [
            (
                "",
                DEFAULT_LOCALIZER,
                [],
            ),
            (
                "- Foo\n- Bar",
                DEFAULT_LOCALIZER,
                [
                    Plain("Foo"),
                    Plain("Bar"),
                ],
            ),
            (
                "Foo -\nBar -",
                Localizer("ar", NullTranslations()),
                [
                    Plain("Foo"),
                    Plain("Bar"),
                ],
            ),
            (
                "- Foo\n  Foo2\n- Bar\n  Bar2",
                DEFAULT_LOCALIZER,
                [
                    Plain("Foo\nFoo2"),
                    Plain("Bar\nBar2"),
                ],
            ),
        ],
    )
    def test_localize(
        self,
        expected: str,
        localizer: Localizer,
        localizables: Sequence[LocalizableLike],
    ) -> None:
        sut = UnorderedList(*localizables)
        assert sut.localize(localizer) == expected


class TestChain:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "FooBar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test(self, expected: str, localizables: Sequence[LocalizableLike]) -> None:
        sut = Chain(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestAnyEnumeration:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo",
                ["Foo"],
            ),
            (
                "Foo, or Bar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test(self, expected: str, localizables: Sequence[LocalizableLike]) -> None:
        sut = AnyEnumeration(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestAllEnumeration:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo",
                ["Foo"],
            ),
            (
                "Foo, and Bar",
                ["Foo", "Bar"],
            ),
        ],
    )
    def test(self, expected: str, localizables: Sequence[LocalizableLike]) -> None:
        sut = AllEnumeration(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


def test_ensure_localizable__with_localizable() -> None:
    localizable = Plain("My First Localizable")
    assert ensure_localizable(localizable) is localizable


def test_ensure_localizable__with_str() -> None:
    localizable = "My First Localizable"
    assert ensure_localizable(localizable).localize(DEFAULT_LOCALIZER) == localizable


def test_ensure_localizable__with_mapping() -> None:
    locale = Locale("nl", "NL")
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        locale: localized,
    }
    assert ensure_localizable(localizable).localize(localizer) == localized


def test_ensure_countable_localizable__with_localizable() -> None:
    localizable = CountableStaticTranslations(
        {
            DEFAULT_LOCALE: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
    )
    assert ensure_countable_localizable(localizable) is localizable


def test_ensure_countable_localizable__with_mapping() -> None:
    localizable: ShorthandCountableStaticTranslations = {
        DEFAULT_LOCALE_TAG: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    }
    assert (
        ensure_countable_localizable(localizable).count(2).localize(DEFAULT_LOCALIZER)
        == "2 worlds"
    )


def test_ensure_localized__with_localizable() -> None:
    localizable = "My First Localizable"
    assert (
        ensure_localized(Plain(localizable), localizer=DEFAULT_LOCALIZER) == localizable
    )


def test_ensure_localized__with_str() -> None:
    localizable = "My First Localizable"
    assert ensure_localized(localizable, localizer=DEFAULT_LOCALIZER) == localizable


def test_ensure_localized__with_mapping() -> None:
    locale = "nl"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        Locale(locale): localized,
    }
    assert ensure_localized(localizable, localizer=localizer) == localized


def test_ensure_localized__with_shorthand_mapping() -> None:
    locale = "nl-NL"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: ShorthandStaticTranslations = {
        DEFAULT_LOCALE_TAG: "My First Localizable",
        locale: localized,
    }
    assert ensure_localized(localizable, localizer=localizer) == localized


class TestRequiredLocalizableAttr:
    class _Instance:
        attr = RequiredLocalizableAttr("attr")

    def test___get____not_initialized(self) -> None:
        instance = self._Instance()
        with pytest.raises(AttrNotInitialized):
            instance.attr  # noqa B018

    def test___set____with_str(self) -> None:
        instance = self._Instance()
        translation = "Hello, world!"
        instance.attr = translation
        assert instance.attr.localize(DEFAULT_LOCALIZER) == translation

    def test___set____with_mapping(self) -> None:
        instance = self._Instance()
        translation = "Hello, world!"
        locale = "nl-NL"
        instance.attr = {
            DEFAULT_LOCALE_TAG: "Hello, world!",
            locale: translation,
        }
        assert (
            instance.attr.localize(Localizer(locale, NullTranslations())) == translation
        )

    def test___set____with_localizable(self) -> None:
        instance = self._Instance()
        localizable = Plain("Hello, world!")
        instance.attr = localizable
        assert instance.attr is localizable


class TestOptionalLocalizableAttr:
    class _Instance:
        attr = OptionalLocalizableAttr("attr")

    def test___get____not_initialized(self) -> None:
        instance = self._Instance()
        assert instance.attr is None

    def test___set____with_str(self) -> None:
        translation = "Hello, world!"
        instance = self._Instance()
        instance.attr = translation
        assert instance.attr is not None
        assert instance.attr.localize(DEFAULT_LOCALIZER) == translation

    def test___set____with_mapping(self) -> None:
        instance = self._Instance()
        translation = "Hello, world!"
        locale = "nl-NL"
        instance.attr = {
            DEFAULT_LOCALE_TAG: "Hello, world!",
            locale: translation,
        }
        assert instance.attr is not None
        assert (
            instance.attr.localize(Localizer(locale, NullTranslations())) == translation
        )

    def test___set____with_localizable(self) -> None:
        instance = self._Instance()
        localizable = Plain("Hello, world!")
        instance.attr = localizable
        assert instance.attr is localizable

    def test___delete____without_value(self) -> None:
        instance = self._Instance()
        del instance.attr
        assert instance.attr is None

    def test___delete____with_value(self) -> None:
        instance = self._Instance()
        instance.attr = "Hello, world!"
        del instance.attr
        assert instance.attr is None


class TestRequiredCountableLocalizableAttr:
    class _Instance:
        attr = RequiredCountableLocalizableAttr("attr")

    def test___get____not_initialized(self) -> None:
        instance = self._Instance()
        with pytest.raises(AttrNotInitialized):
            instance.attr  # noqa B018

    def test___set____with_shorthand(self) -> None:
        instance = self._Instance()
        translation = {
            DEFAULT_LOCALE_TAG: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
        instance.attr = translation
        assert instance.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"

    def test___set____with_mapping(self) -> None:
        instance = self._Instance()
        translation = {
            DEFAULT_LOCALE: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
        instance.attr = translation
        assert instance.attr.count(2).localize(DEFAULT_LOCALIZER) == "2 worlds"
