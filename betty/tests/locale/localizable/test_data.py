import pytest
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.error import UnknownLocale
from betty.locale.localizable import CountableLocalizable, Localizable, LocalizableCount
from betty.locale.localizable.data import (
    CountableLocalizableDefinition,
    LocalizableDefinition,
)
from betty.locale.localizable.error import InvalidPluralTag, MissingPluralTag
from betty.locale.localizable.markup import Paragraph
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import (
    CountableStaticTranslations,
    StaticTranslations,
)
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.portable.error import NotPortable
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestLocalizableDefinition:
    def test_load__without_translations_should_error(self) -> None:
        with pytest.raises(HumanFacingException):
            LocalizableDefinition().load({})

    def test_load__with_single_undetermined_translation(self) -> None:
        localizable = "Hello, world!"
        assert (
            LocalizableDefinition().load(localizable).localize(DEFAULT_LOCALIZER)
            == localizable
        )

    def test_dump__with_plain_text(self) -> None:
        localizable = "Hello, world!"
        assert LocalizableDefinition().dump(Plain(localizable)) == localizable

    def test_dump__with_static_translations_single_undetermined(self) -> None:
        localizable = "Hello, world!"
        assert (
            LocalizableDefinition().dump(StaticTranslations(localizable)) == localizable
        )

    def test_dump__with_static_translations(self) -> None:
        localizable = {
            DEFAULT_LOCALE_TAG: "Hello, world!",
            "nl-NL": "Hallo, wereld!",
        }

        assert (
            LocalizableDefinition().dump(StaticTranslations(localizable)) == localizable
        )

    def test_dump__with_unsupported_localizable(self) -> None:
        with pytest.raises(NotPortable):
            LocalizableDefinition().dump(Paragraph("Hello, world!"))


class _NotDumpableCountableLocalizable(CountableLocalizable):
    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return DUMMY_LOCALIZABLE


class TestCountableLocalizableDefinition:
    def test_load_countable_localizable(self) -> None:
        loaded = CountableLocalizableDefinition().load(
            {
                DEFAULT_LOCALE_TAG: {
                    "one": "{count} thing",
                    "other": "{count} things",
                },
            }
        )
        assert loaded.count(1).localize(DEFAULT_LOCALIZER) == "1 thing"

    def test_load_countable_localizable__without_locales(self) -> None:
        with pytest.raises(HumanFacingException):
            CountableLocalizableDefinition().load({})

    def test_load_countable_localizable__with_unknown_locale(self) -> None:
        with pytest.raises(UnknownLocale):
            CountableLocalizableDefinition().load(
                {
                    "unknownlocale": {},
                }
            )

    def test_load_countable_localizable__with_missing_plural_tag(self) -> None:
        with pytest.raises(MissingPluralTag):
            CountableLocalizableDefinition().load(
                {
                    DEFAULT_LOCALE_TAG: {},
                }
            )

    def test_load_countable_localizable__wth_invalid_plural_tag(self) -> None:
        with pytest.raises(InvalidPluralTag):
            CountableLocalizableDefinition().load(
                {
                    DEFAULT_LOCALE_TAG: {
                        "one": "{count}",
                        "other": "{count}",
                        "invalid": "{count}",
                    },
                }
            )

    def test_dump_countable_localizable(self) -> None:
        assert CountableLocalizableDefinition().dump(
            CountableStaticTranslations(
                {
                    DEFAULT_LOCALE_TAG: {
                        "one": "{count} thing",
                        "other": "{count} things",
                    }
                }
            )
        ) == {
            DEFAULT_LOCALE_TAG: {
                "one": "{count} thing",
                "other": "{count} things",
            }
        }

    class _NotDumpableCountableLocalizable(CountableLocalizable):
        @override
        def count(self, count: LocalizableCount, /) -> Localizable:
            return DUMMY_LOCALIZABLE

    def test_dump_countable_localizable__with_unsupported_localizable(self) -> None:
        with pytest.raises(NotPortable):
            CountableLocalizableDefinition().dump(_NotDumpableCountableLocalizable())
