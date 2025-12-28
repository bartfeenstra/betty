from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

from babel import Locale

from betty.locale import (
    DEFAULT_LOCALE,
    DEFAULT_LOCALE_TAG,
)
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.locale.localize.ensure import ensure_localized

if TYPE_CHECKING:
    from betty.locale.localizable import (
        ShorthandStaticTranslations,
        StaticTranslationsMapping,
    )


def test_ensure_localized__with_localizable() -> None:
    localizable = "My First Localizable"
    assert (
        ensure_localized(Plain(localizable), localizer=DEFAULT_LOCALIZER) == localizable
    )


def test_ensure_localized__with_str() -> None:
    localizable = "My First Localizable"
    assert ensure_localized(localizable, localizer=DEFAULT_LOCALIZER) == localizable


def test_ensure_localized__with_static_translations_mapping() -> None:
    locale = "nl"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: StaticTranslationsMapping = {
        DEFAULT_LOCALE: "My First Localizable",
        Locale(locale): localized,
    }
    assert ensure_localized(localizable, localizer=localizer) == localized


def test_ensure_localized__with_shorthand_static_translations_mapping() -> None:
    locale = "nl-NL"
    localizer = Localizer(locale, NullTranslations())
    localized = "Mijn Eerste, Ja, Wat Eigenlijk?"
    localizable: ShorthandStaticTranslations = {
        DEFAULT_LOCALE_TAG: "My First Localizable",
        locale: localized,
    }
    assert ensure_localized(localizable, localizer=localizer) == localized
