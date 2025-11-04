from typing import TYPE_CHECKING

import pytest

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizable.config import (
    OptionalStaticTranslationsConfigurationAttr,
    RequiredStaticTranslationsConfigurationAttr,
    StaticTranslationsConfiguration,
)
from betty.locale.localizer import DEFAULT_LOCALIZER

if TYPE_CHECKING:
    from betty.serde.dump import Dump


class TestStaticTranslationsConfiguration:
    async def test___getitem__(self) -> None:
        sut = StaticTranslationsConfiguration(
            {DEFAULT_LOCALIZER.locale: "Hello, world!"}
        )
        assert sut[DEFAULT_LOCALIZER.locale] == "Hello, world!"

    async def test___setitem__(self) -> None:
        sut = StaticTranslationsConfiguration(
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
        sut = StaticTranslationsConfiguration(translations)
        assert len(sut) == expected

    async def test_set__without_minimum_translations(self) -> None:
        sut = StaticTranslationsConfiguration(required=True)
        with pytest.raises(HumanFacingException):
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
        sut = StaticTranslationsConfiguration(translations)
        assert sut.localize(DEFAULT_LOCALIZER) == expected

    async def test_localize__with_translations(self) -> None:
        sut = StaticTranslationsConfiguration(
            {DEFAULT_LOCALIZER.locale: "Hello, world!"}
        )
        assert sut.localize(DEFAULT_LOCALIZER) == "Hello, world!"

    async def test_load__without_translations_should_error(self) -> None:
        sut = StaticTranslationsConfiguration()
        with pytest.raises(HumanFacingException):
            sut.load({})

    async def test_load__with_single_undetermined_translation(self) -> None:
        dump = "Hello, world!"
        sut = StaticTranslationsConfiguration()
        sut.load(dump)
        assert sut[UNDETERMINED_LOCALE] == "Hello, world!"

    async def test_load__with_multiple_translations(self) -> None:
        dump: Dump = {
            DEFAULT_LOCALIZER.locale: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }
        sut = StaticTranslationsConfiguration()
        sut.load(dump)
        assert sut[DEFAULT_LOCALIZER.locale] == "Hello, world!"
        assert sut["nl-NL"] == "Hallo, wereld!"

    async def test_dump__without_translations(self) -> None:
        sut = StaticTranslationsConfiguration()
        assert sut.dump() == {}

    async def test_dump__with_single_determined_translation(self) -> None:
        sut = StaticTranslationsConfiguration(
            {
                DEFAULT_LOCALIZER.locale: "Hello, world!",
            }
        )
        assert sut.dump() == {
            DEFAULT_LOCALIZER.locale: "Hello, world!",
        }

    async def test_dump__with_single_undetermined_translation(self) -> None:
        sut = StaticTranslationsConfiguration(
            {
                UNDETERMINED_LOCALE: "Hello, world!",
            }
        )
        assert sut.dump() == "Hello, world!"

    async def test_dump__with_multiple_translations(self) -> None:
        sut = StaticTranslationsConfiguration(
            {
                DEFAULT_LOCALIZER.locale: "Hello, world!",
                "nl-NL": "Hallo, wereld!",
            }
        )
        assert sut.dump() == {
            DEFAULT_LOCALIZER.locale: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }


class TestRequiredStaticTranslationsConfigurationAttr:
    class Instance:
        attr = RequiredStaticTranslationsConfigurationAttr("attr")

    def test___get__(self) -> None:
        instance = self.Instance()
        instance.attr  # noqa B018

    def test___set__(self) -> None:
        translation = "Hello, world!"
        instance = self.Instance()
        instance.attr = translation
        assert instance.attr[UNDETERMINED_LOCALE] == translation


class TestOptionalStaticTranslationsConfigurationAttr:
    class Instance:
        attr = OptionalStaticTranslationsConfigurationAttr("attr")

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
