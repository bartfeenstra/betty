from typing import override

import pytest

from betty.datas.countable_localizable import CountableLocalizableDefinition
from betty.exception import HumanFacingException
from betty.locale import default_locale_tag
from betty.locale.error import UnknownLocale
from betty.locale.localizable import CountableLocalizable, Localizable, LocalizableCount
from betty.locale.localizable.error import InvalidPluralTag, MissingPluralTag
from betty.locale.localizable.static import CountableStaticTranslations
from betty.locale.localize import default_localizer
from betty.portable.error import NotPortable
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class _NotDumpableCountableLocalizable(CountableLocalizable):
    @override
    def count(self, count: LocalizableCount, /) -> Localizable:
        return DUMMY_LOCALIZABLE


class TestCountableLocalizableDefinition:
    def test_load_countable_localizable(self) -> None:
        loaded = CountableLocalizableDefinition().porter.load({
            default_locale_tag: {
                "one": "{count} thing",
                "other": "{count} things",
            },
        })
        assert loaded.count(1).localize(default_localizer) == "1 thing"

    def test_load_countable_localizable__without_locales(self) -> None:
        with pytest.raises(HumanFacingException):
            CountableLocalizableDefinition().porter.load({})

    def test_load_countable_localizable__with_unknown_locale(self) -> None:
        with pytest.raises(UnknownLocale):
            CountableLocalizableDefinition().porter.load({
                "unknownlocale": {},
            })

    def test_load_countable_localizable__with_missing_plural_tag(self) -> None:
        with pytest.raises(MissingPluralTag):
            CountableLocalizableDefinition().porter.load({
                default_locale_tag: {},
            })

    def test_load_countable_localizable__wth_invalid_plural_tag(self) -> None:
        with pytest.raises(InvalidPluralTag):
            CountableLocalizableDefinition().porter.load({
                default_locale_tag: {
                    "one": "{count}",
                    "other": "{count}",
                    "invalid": "{count}",
                },
            })

    def test_dump_countable_localizable(self) -> None:
        assert CountableLocalizableDefinition().porter.dump(
            CountableStaticTranslations({
                default_locale_tag: {
                    "one": "{count} thing",
                    "other": "{count} things",
                }
            })
        ) == {
            default_locale_tag: {
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
            CountableLocalizableDefinition().porter.dump(
                _NotDumpableCountableLocalizable()
            )
