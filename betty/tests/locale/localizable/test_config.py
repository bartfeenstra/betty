import pytest
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.error import UnknownLocale
from betty.locale.localizable import CountableLocalizable, Localizable, LocalizableCount
from betty.locale.localizable.config import (
    dump_countable_localizable,
    dump_localizable,
    load_countable_localizable,
    load_localizable,
)
from betty.locale.localizable.error import InvalidPluralTag, MissingPluralTag
from betty.locale.localizable.markup import Paragraph
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import (
    CountableStaticTranslations,
    StaticTranslations,
)
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.serde import NotDumpable
from betty.test_utils.exception import assert_error
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


async def test_load_localizable__without_translations_should_error() -> None:
    with pytest.raises(HumanFacingException):
        load_localizable({})


async def test_load_localizable__with_single_undetermined_translation() -> None:
    localizable = "Hello, world!"
    assert load_localizable(localizable).localize(DEFAULT_LOCALIZER) == localizable


async def test_dump_localizable__with_plain_text() -> None:
    localizable = "Hello, world!"
    assert dump_localizable(Plain(localizable)) == localizable


async def test_dump_localizable__with_static_translations_single_undetermined() -> None:
    localizable = "Hello, world!"
    assert dump_localizable(StaticTranslations(localizable)) == localizable


async def test_dump_localizable__with_static_translations() -> None:
    localizable = {
        DEFAULT_LOCALE_TAG: "Hello, world!",
        "nl-NL": "Hallo, wereld!",
    }

    assert dump_localizable(StaticTranslations(localizable)) == localizable


async def test_dump_localizable__with_unsupported_localizable() -> None:
    with pytest.raises(NotDumpable):
        dump_localizable(Paragraph("Hello, world!"))


def test_load_countable_localizable() -> None:
    loaded = load_countable_localizable(
        {
            DEFAULT_LOCALE_TAG: {
                "one": "{count} thing",
                "other": "{count} things",
            },
        }
    )
    assert loaded.count(1).localize(DEFAULT_LOCALIZER) == "1 thing"


def test_load_countable_localizable__without_locales() -> None:
    with pytest.raises(HumanFacingException):
        load_countable_localizable({})


def test_load_countable_localizable__with_unknown_locale() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        load_countable_localizable(
            {
                "unknownlocale": {},
            }
        )
    assert_error(exc_info.value, error_type=UnknownLocale)


def test_load_countable_localizable__with_missing_plural_tag() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        load_countable_localizable(
            {
                DEFAULT_LOCALE_TAG: {},
            }
        )
    assert_error(exc_info.value, error_type=MissingPluralTag)


def test_load_countable_localizable__wth_invalid_plural_tag() -> None:
    with pytest.raises(HumanFacingException) as exc_info:
        load_countable_localizable(
            {
                DEFAULT_LOCALE_TAG: {
                    "one": "{count}",
                    "other": "{count}",
                    "invalid": "{count}",
                },
            }
        )
    assert_error(exc_info.value, error_type=InvalidPluralTag)


def test_dump_countable_localizable() -> None:
    assert dump_countable_localizable(
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


def test_dump_countable_localizable__with_unsupported_localizable() -> None:
    with pytest.raises(NotDumpable):
        dump_countable_localizable(_NotDumpableCountableLocalizable())
