from typing import TYPE_CHECKING, Sequence

import pytest
from betty.assertion.error import AssertionFailed
from betty.locale import UNDETERMINED_LOCALE, DEFAULT_LOCALE
from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizable.assertion import assert_static_translations
from betty.locale.localizable.config import (
    StaticTranslationsLocalizableConfiguration,
    StaticTranslationsLocalizableConfigurationAttr,
)
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.test_utils.attr import MutableAttrTestBase
from betty.typing import Void
from typing_extensions import override

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestStaticTranslationsLocalizableConfiguration:
    async def test___getitem__(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration(
            {DEFAULT_LOCALIZER.locale: "Hello, world!"}
        )
        assert sut[DEFAULT_LOCALIZER.locale] == "Hello, world!"

    async def test___setitem__(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration(
            {DEFAULT_LOCALIZER.locale: "Hello, world!"}
        )
        sut[DEFAULT_LOCALIZER.locale] = "Hello, other world!"
        assert sut[DEFAULT_LOCALIZER.locale] == "Hello, other world!"

    @pytest.mark.parametrize(
        ("expected", "translations"),
        [
            (0, None),
            (1, "Hello, world!"),
            (1, {DEFAULT_LOCALE: "Hello, world!"}),
            (2, {DEFAULT_LOCALE: "Hello, world!", "nl-NL": "Hallo, wereld!"}),
        ],
    )
    async def test___len__(
        self, expected: int, translations: ShorthandStaticTranslations | None
    ) -> None:
        sut = StaticTranslationsLocalizableConfiguration(translations)
        assert len(sut) == expected

    @pytest.mark.parametrize(
        ("expected", "translations"),
        [
            ("Hello, world!", "Hello, world!"),
            ("Hello, world!", {DEFAULT_LOCALE: "Hello, world!"}),
            (
                "Hello, world!",
                {DEFAULT_LOCALE: "Hello, world!", "nl-NL": "Hallo, wereld!"},
            ),
        ],
    )
    async def test_set(
        self, expected: str, translations: ShorthandStaticTranslations
    ) -> None:
        sut = StaticTranslationsLocalizableConfiguration()
        sut.set(translations)
        assert sut.localize(DEFAULT_LOCALIZER) == expected

    async def test_set_without_minimum_translations(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration(required=True)
        with pytest.raises(AssertionFailed):
            sut.set({})

    @pytest.mark.parametrize(
        ("expected", "translations"),
        [
            ("Hello, world!", "Hello, world!"),
            ("Hello, world!", {DEFAULT_LOCALE: "Hello, world!"}),
            (
                "Hello, world!",
                {DEFAULT_LOCALE: "Hello, world!", "nl-NL": "Hallo, wereld!"},
            ),
        ],
    )
    async def test___init__(
        self, expected: str, translations: ShorthandStaticTranslations
    ) -> None:
        sut = StaticTranslationsLocalizableConfiguration(translations)
        assert sut.localize(DEFAULT_LOCALIZER) == expected

    async def test_localize_with_translations(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration(
            {DEFAULT_LOCALIZER.locale: "Hello, world!"}
        )
        assert sut.localize(DEFAULT_LOCALIZER) == "Hello, world!"

    async def test_update(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration()
        other = StaticTranslationsLocalizableConfiguration(
            {DEFAULT_LOCALIZER.locale: "Hello, world!"}
        )
        sut.update(other)
        assert sut[DEFAULT_LOCALIZER.locale] == "Hello, world!"

    async def test_load_without_translations_should_error(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration()
        with pytest.raises(AssertionFailed):
            sut.load({})

    async def test_load_with_single_undetermined_translation(self) -> None:
        dump = "Hello, world!"
        sut = StaticTranslationsLocalizableConfiguration()
        sut.load(dump)
        assert sut[UNDETERMINED_LOCALE] == "Hello, world!"

    async def test_load_with_multiple_translations(self) -> None:
        dump: Dump = {
            DEFAULT_LOCALIZER.locale: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }
        sut = StaticTranslationsLocalizableConfiguration()
        sut.load(dump)
        assert sut[DEFAULT_LOCALIZER.locale] == "Hello, world!"
        assert sut["nl-NL"] == "Hallo, wereld!"

    async def test_dump_without_translations(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration()
        assert sut.dump() is Void

    async def test_dump_with_single_determined_translation(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration(
            {
                DEFAULT_LOCALIZER.locale: "Hello, world!",
            }
        )
        assert sut.dump() == {
            DEFAULT_LOCALIZER.locale: "Hello, world!",
        }

    async def test_dump_with_single_undetermined_translation(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration(
            {
                UNDETERMINED_LOCALE: "Hello, world!",
            }
        )
        assert sut.dump() == "Hello, world!"

    async def test_dump_with_multiple_translations(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration(
            {
                DEFAULT_LOCALIZER.locale: "Hello, world!",
                "nl-NL": "Hallo, wereld!",
            }
        )
        assert sut.dump() == {
            DEFAULT_LOCALIZER.locale: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }


class TestStaticTranslationsLocalizableConfigurationAttr(
    MutableAttrTestBase[
        object, StaticTranslationsLocalizableConfiguration, ShorthandStaticTranslations
    ]
):
    @override
    def get_mutable_instances(
        self,
    ) -> tuple[Sequence[tuple[object, Sequence[ShorthandStaticTranslations]]], str]:
        class Instance:
            attr = StaticTranslationsLocalizableConfigurationAttr(
                "attr", required=False
            )

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
        get_value: StaticTranslationsLocalizableConfiguration,
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
