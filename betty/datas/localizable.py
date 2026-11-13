"""
Localizable data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.assertions.if_else import assert_if_else
from betty.assertions.locale import assert_locale
from betty.assertions.mapping import assert_mapping
from betty.assertions.str import assert_str
from betty.data import DataDefinition
from betty.importlib import fully_qualified_name
from betty.locale import to_language_tag
from betty.localizable import CountableLocalizable
from betty.localizables.gettext import _
from betty.localizables.static import (
    CountableStaticTranslations,
    StaticTranslations,
)
from betty.localized import LocalizedStr
from betty.localizer import AnyLocalizable
from betty.portable import Porter
from betty.portable.error import NotDumpable

if TYPE_CHECKING:
    from betty.portable import PortableData


@final
class LocalizableDefinition(DataDefinition[AnyLocalizable]):
    """
    The data definition for :py:class:`betty.localizer.AnyLocalizable`.
    """

    def __init__(self):
        super().__init__(label=_("A localizable string"), porter=_LocalizablePorter())


class _LocalizablePorter(Porter[AnyLocalizable]):
    _load = assert_if_else(
        assert_str(minimum_length=1),
        assert_mapping(
            assert_str(minimum_length=1),
            lambda key: None if key == "" else assert_locale(key),
        ),
    )

    @override
    def load(self, data: PortableData, /) -> AnyLocalizable:
        translations = self._load(data)
        if isinstance(translations, str):
            return LocalizedStr(translations)
        if len(translations) == 1:
            locale, translation = next(iter(translations.items()))
            return LocalizedStr(translation, locale=locale)
        return StaticTranslations(translations)

    @override
    def dump(self, data: AnyLocalizable) -> PortableData:
        if isinstance(data, str):
            return {
                to_language_tag(data.locale)
                if isinstance(data, LocalizedStr)
                else "": data,
            }
        if not isinstance(data, StaticTranslations):
            raise NotDumpable(
                f"Only {fully_qualified_name(StaticTranslations)} and {fully_qualified_name(str)} can be dumped to portable data, not `{fully_qualified_name(data)}` objects."
            )
        if len(data.translations) == 1 and None in data.translations:
            return data.translations[None]
        return {
            to_language_tag(locale): translation
            for locale, translation in data.translations.items()
        }


@final
class CountableLocalizableDefinition(DataDefinition[CountableLocalizable]):
    """
    The data definition for :py:class:`betty.localizable.CountableLocalizable`.
    """

    def __init__(self):
        super().__init__(
            label=_("A countable localizable string"),
            porter=_CountableLocalizablePorter(),
        )


class _CountableLocalizablePorter(Porter[CountableLocalizable]):
    load = override(
        assert_mapping(assert_mapping(assert_str(), assert_str()), assert_locale)
        | CountableStaticTranslations  # ty: ignore[unsupported-operator]
    )

    @override
    def dump(self, data: CountableLocalizable) -> PortableData:
        if not isinstance(data, CountableStaticTranslations):
            raise NotDumpable(
                f"Only {fully_qualified_name(CountableStaticTranslations)} and {fully_qualified_name(str)} can be dumped to portable data, not `{fully_qualified_name(data)}` objects."
            )
        return {
            to_language_tag(locale): translations
            for locale, translations in data.translations.items()
        }
