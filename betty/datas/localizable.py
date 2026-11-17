"""
Localizable data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast, final, override

from betty.data import DataDefinition
from betty.importlib import fully_qualified_name
from betty.locale import to_language_tag
from betty.localizable import CountableLocalizable
from betty.localizables.gettext import _
from betty.localizables.static import (
    CountableStaticTranslations,
    StaticTranslations,
    StaticTranslationsMapping,
)
from betty.localized import LocalizedStr
from betty.localizer import AnyLocalizable
from betty.portable import Porter
from betty.portable.error import NotDumpable
from betty.validators.group import is_any
from betty.validators.locale import is_locale
from betty.validators.mapping import is_mapping
from betty.validators.none import is_optional
from betty.validators.str import is_str

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
    load = override(
        is_any(
            is_str
            | (
                lambda translation: cast(StaticTranslationsMapping, {None: translation})
            ),
            is_mapping(keys=is_optional(is_locale), values=is_str),
        )
        | StaticTranslations
    )

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
                message=f"Only static translations and plain text can be dumped to portable data, not `{fully_qualified_name(data)}`."
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
        is_mapping(
            keys=is_optional(is_locale), values=is_mapping(keys=is_str, values=is_str)
        )
        | CountableStaticTranslations  # ty: ignore[unsupported-operator]
    )

    @override
    def dump(self, data: CountableLocalizable) -> PortableData:
        if not isinstance(data, CountableStaticTranslations):
            raise NotDumpable(
                message=f"Only static translations and plain text can be dumped to portable data, not `{fully_qualified_name(data)}`."
            )
        return {
            to_language_tag(locale): translations
            for locale, translations in data.translations.items()
        }
