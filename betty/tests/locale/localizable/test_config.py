from typing import TYPE_CHECKING

import pytest

from betty.assertion.error import AssertionFailed
from betty.locale import UNDETERMINED_LOCALE, DEFAULT_LOCALE
from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizable.config import (
    StaticTranslationsLocalizableConfiguration,
    OptionalStaticTranslationsLocalizableConfigurationAttr,
    RequiredStaticTranslationsLocalizableConfigurationAttr,
)
from betty.locale.localizer import DEFAULT_LOCALIZER

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

    async def test_set_without_minimum_translations(self) -> None:
        sut = StaticTranslationsLocalizableConfiguration(required=True)
        with pytest.raises(AssertionFailed):
            sut.replace({})

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
        assert sut.dump() == {}

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


class TestRequiredStaticTranslationsLocalizableConfigurationAttr:
    class Instance:
        attr = RequiredStaticTranslationsLocalizableConfigurationAttr("attr")

    def test___get__(self) -> None:
        instance = self.Instance()
        instance.attr  # noqa B018

    def test___set__(self) -> None:
        translation = "Hello, world!"
        instance = self.Instance()
        instance.attr = translation
        assert instance.attr[UNDETERMINED_LOCALE] == translation


class TestOptionalStaticTranslationsLocalizableConfigurationAttr:
    class Instance:
        attr = OptionalStaticTranslationsLocalizableConfigurationAttr("attr")

    def test___get__(self) -> None:
        instance = self.Instance()
        instance.attr  # noqa B018

    def test___set__(self) -> None:
        translation = "Hello, world!"
        instance = self.Instance()
        instance.attr = translation
        assert instance.attr[UNDETERMINED_LOCALE] == translation

    def test___delete__(self) -> None:
        translation = "Hello, world!"
        instance = self.Instance()
        instance.attr = translation
        del instance.attr
        with pytest.raises(KeyError):
            instance.attr[UNDETERMINED_LOCALE]  # noqa B018
