from collections.abc import Callable, Iterable, Sequence
from gettext import NullTranslations
from typing import cast

import pytest
from typing_extensions import override

from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import (
    AllEnumeration,
    AnyEnumeration,
    Chain,
    CountableLocalizable,
    CountablePlain,
    Lines,
    Localizable,
    OrderedList,
    Paragraph,
    Paragraphs,
    Plain,
    ShorthandStaticTranslations,
    StaticTranslations,
    StaticTranslationsMapping,
    StaticTranslationsSchema,
    UnorderedList,
    do_you_mean,
    ensure_localizable,
    ensure_localized,
)
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.serde.dump import Dump, DumpMapping
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut


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

    def test___getitem__(self) -> None:
        locale = "nl-NL"
        translation = "Hallo, wereld!"
        sut = StaticTranslations(
            {
                DEFAULT_LOCALE: "Hello, world!",
                locale: translation,
            }
        )
        assert sut[locale] == translation

    def test___setitem__(self) -> None:
        locale = "nl-NL"
        translation = "Hallo, wereld!"
        sut = StaticTranslations({DEFAULT_LOCALE: "Hello, world!"})
        sut[locale] = translation
        assert sut[locale] == translation

    @pytest.mark.parametrize(
        ("expected", "translations"),
        [
            (
                0,
                {},
            ),
            (
                1,
                "Hello, world!",
            ),
            (
                1,
                {
                    "en-US": "Hello, world!",
                },
            ),
            (
                2,
                {
                    "nl-NL": "Hallo, wereld!",
                    "en": "Hello, world!",
                },
            ),
        ],
    )
    async def test___len__(
        self, expected: int, translations: ShorthandStaticTranslations
    ) -> None:
        sut = StaticTranslations(translations, required=False)
        assert len(sut) == expected

    @pytest.mark.parametrize(
        ("expected", "translations"),
        [
            (
                {},
                {},
            ),
            (
                {UNDETERMINED_LOCALE: "Hello, world!"},
                "Hello, world!",
            ),
            (
                {
                    "en-US": "Hello, world!",
                },
                {
                    "en-US": "Hello, world!",
                },
            ),
            (
                {
                    "nl-NL": "Hallo, wereld!",
                    "en": "Hello, world!",
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
        sut = StaticTranslations(translations, required=False)
        assert sut.translations == expected

    def test_replace(self) -> None:
        translation = "Hallo, wereld!"
        sut = StaticTranslations(required=False)
        sut.replace(translation)
        assert sut.localize(DEFAULT_LOCALIZER) == translation

    @pytest.mark.parametrize(
        ("expected", "translations"),
        [
            (
                {},
                {},
            ),
            (
                {UNDETERMINED_LOCALE: "Hello, world!"},
                "Hello, world!",
            ),
            (
                {"en-US": "Hello, world!"},
                {
                    "en-US": "Hello, world!",
                },
            ),
            (
                {"nl-NL": "Hallo, wereld!", "en": "Hello, world!"},
                {
                    "nl-NL": "Hallo, wereld!",
                    "en": "Hello, world!",
                },
            ),
        ],
    )
    async def test_dump_linked_data(
        self,
        expected: DumpMapping[Dump],
        translations: ShorthandStaticTranslations,
    ) -> None:
        sut = StaticTranslations(translations, required=False)
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected


class TestStaticTranslationsSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[SchemaTestBaseSut]:
        valid_datas: Sequence[Dump] = [
            {DEFAULT_LOCALE: "Hello, world!"},
            {"nl": "Hallo, wereld!", "uk": "Привіт Світ!"},
        ]
        invalid_datas: Sequence[Dump] = [
            True,
            False,
            None,
            123,
            [],
            {DEFAULT_LOCALE: True},
            {DEFAULT_LOCALE: False},
            {DEFAULT_LOCALE: None},
            {DEFAULT_LOCALE: 123},
            {DEFAULT_LOCALE: []},
            {DEFAULT_LOCALE: {}},
        ]
        return [
            (
                StaticTranslationsSchema(),
                valid_datas,
                invalid_datas,
            ),
        ]

    @override
    @pytest.fixture(params=_sut_params())
    def sut(self, request: pytest.FixtureRequest) -> SchemaTestBaseSut:
        return cast(SchemaTestBaseSut, request.param)


class TestPlain:
    @pytest.mark.parametrize(
        "string",
        [
            "Hello, world!",
            "Hallo, wereld!",
        ],
    )
    async def test_localize(self, string: str) -> None:
        assert Plain(string).localize(DEFAULT_LOCALIZER) == string


class TestCountablePlain:
    @pytest.mark.parametrize(
        (
            "expected",
            "string_singular",
            "string_plural",
            "locale",
            "is_plural",
            "count",
        ),
        [
            (
                "Hello, worlds!",
                "Hello, world!",
                "Hello, worlds!",
                DEFAULT_LOCALE,
                None,
                0,
            ),
            (
                "Hello, world!",
                "Hello, world!",
                "Hello, worlds!",
                DEFAULT_LOCALE,
                None,
                1,
            ),
            (
                "Hello, worlds!",
                "Hello, world!",
                "Hello, worlds!",
                DEFAULT_LOCALE,
                None,
                2,
            ),
            (
                "Hello, world!",
                "Hello, world!",
                "Hello, worlds!",
                DEFAULT_LOCALE,
                lambda count: count > 1,
                0,
            ),
            (
                "Hello, world!",
                "Hello, world!",
                "Hello, worlds!",
                DEFAULT_LOCALE,
                lambda count: count > 1,
                1,
            ),
            (
                "Hello, worlds!",
                "Hello, world!",
                "Hello, worlds!",
                DEFAULT_LOCALE,
                lambda count: count > 1,
                2,
            ),
        ],
    )
    async def test_count(
        self,
        expected: str,
        string_singular: str,
        string_plural: str,
        locale: str,
        is_plural: Callable[[int], bool] | None,
        count: int,
    ) -> None:
        assert (
            CountablePlain(
                string_singular, string_plural, locale=locale, is_plural=is_plural
            )
            .count(count)
            .localize(DEFAULT_LOCALIZER)
            == expected
        )


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
        def count(self, count: int, /) -> Localizable:
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
                [Plain("Foo"), Plain("Bar")],
            ),
        ],
    )
    def test_localize(self, expected: str, localizables: Sequence[Localizable]) -> None:
        sut = Lines(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestParagraph:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo Bar",
                [Plain("Foo"), Plain("Bar")],
            ),
        ],
    )
    def test_localize(self, expected: str, localizables: Sequence[Localizable]) -> None:
        sut = Paragraph(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestParagraphs:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo\n\nBar",
                [Plain("Foo"), Plain("Bar")],
            ),
        ],
    )
    def test_localize(self, expected: str, localizables: Sequence[Localizable]) -> None:
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
                [Plain("Foo"), Plain("Bar")],
            ),
            (
                "Foo .1\nBar .2",
                Localizer("ar", NullTranslations()),
                [Plain("Foo"), Plain("Bar")],
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
        self, expected: str, localizer: Localizer, localizables: Sequence[Localizable]
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
        self, expected: str, localizer: Localizer, localizables: Sequence[Localizable]
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
                [Plain("Foo"), Plain("Bar")],
            ),
        ],
    )
    def test(self, expected: str, localizables: Sequence[Localizable]) -> None:
        sut = Chain(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestAnyEnumeration:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo",
                [Plain("Foo")],
            ),
            (
                "Foo, or Bar",
                [Plain("Foo"), Plain("Bar")],
            ),
        ],
    )
    def test(self, expected: str, localizables: Sequence[Localizable]) -> None:
        sut = AnyEnumeration(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


class TestAllEnumeration:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            (
                "Foo",
                [Plain("Foo")],
            ),
            (
                "Foo, and Bar",
                [Plain("Foo"), Plain("Bar")],
            ),
        ],
    )
    def test(self, expected: str, localizables: Sequence[Localizable]) -> None:
        sut = AllEnumeration(*localizables)
        assert sut.localize(DEFAULT_LOCALIZER) == expected


def test_ensure_localizable__with_localizable() -> None:
    localizable = Plain("My First Localizable")
    assert ensure_localizable(localizable) is localizable


def test_ensure_localizable__with_str() -> None:
    localizable = "My First Localizable"
    assert ensure_localizable(localizable).localize(DEFAULT_LOCALIZER) == localizable


def test_ensure_localizable__with_static_translations_mapping() -> None:
    locale = "nl-NL"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        locale: localized,
    }
    assert ensure_localizable(localizable).localize(localizer) == localized


def test_ensure_localized__with_localizable() -> None:
    localizable = "My First Localizable"
    assert (
        ensure_localized(Plain(localizable), localizer=DEFAULT_LOCALIZER) == localizable
    )


def test_ensure_localized__with_str() -> None:
    localizable = "My First Localizable"
    assert ensure_localized(localizable, localizer=DEFAULT_LOCALIZER) == localizable


def test_ensure_localized__with_static_translations_mapping() -> None:
    locale = "nl-NL"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        locale: localized,
    }
    assert ensure_localized(localizable, localizer=localizer) == localized
