from gettext import NullTranslations

from babel import Locale
from typing_extensions import override

from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable import (
    CountableLocalizable,
    Localizable,
    LocalizableCount,
    ShorthandCountableStaticTranslations,
    StaticTranslationsMapping,
    resolve_countable_localizable,
    resolve_localizable,
)
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import CountableStaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer


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


def test_resolve_localizable__with_localizable() -> None:
    localizable = Plain("My First Localizable")
    assert resolve_localizable(localizable) is localizable


def test_resolve_localizable__with_str() -> None:
    localizable = "My First Localizable"
    assert resolve_localizable(localizable).localize(DEFAULT_LOCALIZER) == localizable


def test_resolve_localizable__with_mapping() -> None:
    locale = Locale("nl", "NL")
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        locale: localized,
    }
    assert resolve_localizable(localizable).localize(localizer) == localized


def test_resolve_countable_localizable__with_localizable() -> None:
    localizable = CountableStaticTranslations(
        {
            DEFAULT_LOCALE: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
    )
    assert resolve_countable_localizable(localizable) is localizable


def test_resolve_countable_localizable__with_mapping() -> None:
    localizable: ShorthandCountableStaticTranslations = {
        DEFAULT_LOCALE_TAG: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    }
    assert (
        resolve_countable_localizable(localizable).count(2).localize(DEFAULT_LOCALIZER)
        == "2 worlds"
    )
