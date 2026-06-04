from gettext import NullTranslations
from typing import override

from babel import Locale

from betty.locale import default_locale, default_locale_tag
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
from betty.locale.localize import Localizer, default_localizer


class TestCountableLocalizable:
    class _Sut(CountableLocalizable):
        @override
        def count(self, count: LocalizableCount, /) -> Localizable:
            return Plain("{format_placeholder}")

    def test_format(self) -> None:
        sut = self._Sut()
        assert (
            sut
            .count(9)
            .format(format_placeholder="format-value")
            .localize(default_localizer)
            == "format-value"
        )


def test_resolve_localizable__with_localizable() -> None:
    localizable = Plain("My First Localizable")
    assert resolve_localizable(localizable) is localizable


def test_resolve_localizable__with_str() -> None:
    localizable = "My First Localizable"
    assert resolve_localizable(localizable).localize(default_localizer) == localizable


def test_resolve_localizable__with_mapping() -> None:
    locale = Locale("nl", "NL")
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        default_locale: "My First Localizable",
        locale: localized,
    }
    assert resolve_localizable(localizable).localize(localizer) == localized


def test_resolve_countable_localizable__with_localizable() -> None:
    localizable = CountableStaticTranslations({
        default_locale: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    })
    assert resolve_countable_localizable(localizable) is localizable


def test_resolve_countable_localizable__with_mapping() -> None:
    localizable: ShorthandCountableStaticTranslations = {
        default_locale_tag: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    }
    assert (
        resolve_countable_localizable(localizable).count(2).localize(default_localizer)
        == "2 worlds"
    )
