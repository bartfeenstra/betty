"""
Locale properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from babel import Locale

from betty.datas.locale import LocaleDefinition
from betty.linked_data import LinkedDataDumper
from betty.locale import (
    LOCALE_SCHEMA,
    Localized,
    ResolvableLocale,
    resolve_locale,
    to_language_tag,
)
from betty.property import Optional, Property

if TYPE_CHECKING:
    from betty.json_schema import Schema
    from betty.locale.localizable import ResolvableLocalizable
    from betty.project import Project


@final
class LocaleProperty(Property, LinkedDataDumper[Locale, str]):
    """
    A property containing a locale.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            LocaleDefinition(),
            label=label,
            description=description,
            resolver=resolve_locale,
        )

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        return LOCALE_SCHEMA

    @override
    async def dump_linked_data_for(self, project: Project, target: Locale, /) -> str:
        return to_language_tag(target)


class HasLocale(Localized):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    locale = Optional(LocaleProperty())

    def __init__(
        self, *args: Any, locale: ResolvableLocale | None = None, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.locale = locale
