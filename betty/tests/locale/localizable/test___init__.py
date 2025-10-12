from collections.abc import Callable, Sequence
from gettext import NullTranslations

import pytest
from typing_extensions import override

from betty.json.schema import Schema
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import (
    CountableLocalizable,
    CountablePlain,
    Join,
    Localizable,
    Plain,
    ShorthandStaticTranslations,
    StaticTranslations,
    StaticTranslationsMapping,
    StaticTranslationsSchema,
    do_you_mean,
)
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.serde.dump import Dump, DumpMapping
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from betty.test_utils.json.schema import SchemaTestBase


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
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
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


class TestJoin:
    @pytest.mark.parametrize(
        ("expected", "localizables"),
        [
            ("", []),
            ("foo", [Plain("foo")]),
            ("foo bar baz", [Plain("foo"), Plain("bar"), Plain("baz")]),
        ],
    )
    async def test_localize(
        self, expected: str, localizables: Sequence[Localizable]
    ) -> None:
        assert Join(" ", *localizables).localize(DEFAULT_LOCALIZER) == expected


@pytest.mark.parametrize(
    ("expected", "available_options"),
    [
        ("There are no available options.", []),
        ("Do you mean foo?", ["foo"]),
        ("Do you mean one of bar, baz, foo?", ["foo", "bar", "baz"]),
    ],
)
async def test_do_you_mean(expected: str, available_options: Sequence[str]) -> None:
    assert do_you_mean(*available_options).localize(DEFAULT_LOCALIZER) == expected


class TestCountableLocalizable:
    class _Sut(CountableLocalizable):
        @override
        def count(self, count: int) -> Localizable:
            return Plain("{format_placeholder}")

    def test_format(self) -> None:
        sut = self._Sut()
        assert (
            sut.count(9)
            .format(format_placeholder="format-value")
            .localize(DEFAULT_LOCALIZER)
            == "format-value"
        )
