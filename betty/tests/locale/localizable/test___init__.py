from collections.abc import Sequence
from gettext import NullTranslations

import pytest

from betty.json.schema import Schema
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import (
    StaticTranslationsLocalizable,
    plain,
    StaticTranslationsLocalizableAttr,
    StaticTranslations,
    StaticTranslationsLocalizableSchema,
)
from betty.locale.localizable import (
    static,
    ShorthandStaticTranslations,
)
from betty.locale.localizable.assertion import assert_static_translations
from betty.locale.localizer import Localizer, DEFAULT_LOCALIZER
from betty.serde.dump import Dump, DumpMapping
from betty.test_utils.attr import MutableAttrTestBase
from betty.test_utils.json.linked_data import assert_dumps_linked_data
from typing_extensions import override

from betty.test_utils.json.schema import SchemaTestBase


class TestStaticTranslationsLocalizable:
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

    def test___getitem__(self) -> None:
        locale = "nl-NL"
        translation = "Hallo, wereld!"
        sut = StaticTranslationsLocalizable(
            {
                DEFAULT_LOCALE: "Hello, world!",
                locale: translation,
            }
        )
        assert sut[locale] == translation

    def test___setitem__(self) -> None:
        locale = "nl-NL"
        translation = "Hallo, wereld!"
        sut = StaticTranslationsLocalizable({DEFAULT_LOCALE: "Hello, world!"})
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
        sut = StaticTranslationsLocalizable(translations, required=False)
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
        self, expected: StaticTranslations, translations: ShorthandStaticTranslations
    ) -> None:
        sut = StaticTranslationsLocalizable(translations, required=False)
        assert sut.translations == expected

    def test_replace(self) -> None:
        translation = "Hallo, wereld!"
        sut = StaticTranslationsLocalizable(required=False)
        sut.replace(translation)
        assert sut.localize(DEFAULT_LOCALIZER) == translation

    @pytest.mark.parametrize(
        ("expected", "translations"),
        [
            (
                {"translations": {}},
                {},
            ),
            (
                {
                    "translations": {
                        UNDETERMINED_LOCALE: "Hello, world!",
                    }
                },
                "Hello, world!",
            ),
            (
                {
                    "translations": {
                        "en-US": "Hello, world!",
                    }
                },
                {
                    "en-US": "Hello, world!",
                },
            ),
            (
                {
                    "translations": {
                        "nl-NL": "Hallo, wereld!",
                        "en": "Hello, world!",
                    }
                },
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
        sut = StaticTranslationsLocalizable(translations, required=False)
        actual = await assert_dumps_linked_data(sut)
        assert actual == expected


class TestStaticTranslationsLocalizableSchema(SchemaTestBase):
    @override
    async def get_sut_instances(self) -> Sequence[tuple[Schema, Sequence[Dump]]]:
        translations: Sequence[Dump] = [
            {DEFAULT_LOCALE: "Hello, world!"},
            {"nl": "Hallo, wereld!", "uk": "Привіт Світ!"},
        ]
        return [
            (
                StaticTranslationsLocalizableSchema(),
                translations,
            ),
        ]


class TestStaticTranslationsLocalizableAttr(
    MutableAttrTestBase[
        object, StaticTranslationsLocalizable, ShorthandStaticTranslations
    ]
):
    @override
    def get_mutable_instances(
        self,
    ) -> tuple[Sequence[tuple[object, Sequence[ShorthandStaticTranslations]]], str]:
        class Instance:
            attr = StaticTranslationsLocalizableAttr("attr", required=False)

        return [
            (
                Instance(),
                [
                    "Hello, world!",
                    {
                        DEFAULT_LOCALE: "Hello, world!",
                    },
                ],
            )
        ], "attr"

    @override
    def assert_eq(
        self,
        get_value: StaticTranslationsLocalizable,
        set_value: ShorthandStaticTranslations,
    ) -> None:
        assert get_value._translations == assert_static_translations()(set_value)

    @override
    def test_new_attr(self) -> None:
        instances, attr_name = self.get_mutable_instances()
        for instance, _ in instances:
            assert isinstance(
                getattr(type(instance), attr_name).new_attr(instance),
                type(getattr(instance, attr_name)),
            )


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


class TestPlain:
    @pytest.mark.parametrize(
        "string",
        [
            "Hello, world!",
            "Hallo, wereld!",
        ],
    )
    async def test(self, string: str) -> None:
        assert plain(string).localize(DEFAULT_LOCALIZER) == string
