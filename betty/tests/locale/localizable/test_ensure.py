from gettext import NullTranslations
from typing import TYPE_CHECKING

from babel import Locale

from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable.ensure import (
    ensure_countable_localizable,
    ensure_localizable,
)
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import CountableStaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer

if TYPE_CHECKING:
    from betty.locale.localizable import (
        ShorthandCountableStaticTranslations,
        StaticTranslationsMapping,
    )


def test_ensure_localizable__with_localizable() -> None:
    localizable = Plain("My First Localizable")
    assert ensure_localizable(localizable) is localizable


def test_ensure_localizable__with_str() -> None:
    localizable = "My First Localizable"
    assert ensure_localizable(localizable).localize(DEFAULT_LOCALIZER) == localizable


def test_ensure_localizable__with_mapping() -> None:
    locale = Locale("nl", "NL")
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        locale: localized,
    }
    assert ensure_localizable(localizable).localize(localizer) == localized


def test_ensure_countable_localizable__with_localizable() -> None:
    localizable = CountableStaticTranslations(
        {
            DEFAULT_LOCALE: {
                "one": "{count} world",
                "other": "{count} worlds",
            },
        }
    )
    assert ensure_countable_localizable(localizable) is localizable


def test_ensure_countable_localizable__with_mapping() -> None:
    localizable: ShorthandCountableStaticTranslations = {
        DEFAULT_LOCALE_TAG: {
            "one": "{count} world",
            "other": "{count} worlds",
        },
    }
    assert (
        ensure_countable_localizable(localizable).count(2).localize(DEFAULT_LOCALIZER)
        == "2 worlds"
    )
