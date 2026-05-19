"""
Locale attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attrs.attr import AttrAttr
from betty.datas.locale import LocaleDefinition
from betty.json_schema import Null, OneOf
from betty.linked_data import JsonLdObject, LinkedDataDumpableWithSchemaJsonLdObject
from betty.locale import Localized, ResolvableLocale, resolve_locale, to_language_tag
from betty.locale.schema import LocaleSchema
from betty.privacy.resolve import is_public
from betty.property import HasProperties

if TYPE_CHECKING:
    from babel import Locale

    from betty.attrs.owner import OwnerAttr
    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


def new_locale_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> OwnerAttr[HasProperties, Locale, ResolvableLocale]:
    """
    Create an attribute containing a locale.
    """
    return AttrAttr(LocaleDefinition(), label=label, description=description).setter(
        resolve_locale
    )


class HasLocale(Localized, LinkedDataDumpableWithSchemaJsonLdObject, HasProperties):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    locale = new_locale_attr().optional

    def __init__(
        self, *args: Any, locale: ResolvableLocale | None = None, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.locale = locale

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        portable["locale"] = to_language_tag(self.locale) if is_public(self) else None
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("locale", OneOf(LocaleSchema(), Null()))
        return schema
