"""
Locale attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attrs.owner import OwnerAttr
from betty.attrs.privacy import HasPrivacy
from betty.datas.locale import LocaleDefinition
from betty.json_schema import Null, OneOf
from betty.json_schemas.locale import LocaleSchema
from betty.linked_data import JsonLdObject, LinkedDataDumpableWithSchemaJsonLdObject
from betty.locale import ResolvableLocale, resolve_locale, to_language_tag
from betty.localized import Localized
from betty.prop import HasProps

if TYPE_CHECKING:
    from babel import Locale

    from betty.attrs.common import OptionableCommonAttr
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


def new_locale_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> OptionableCommonAttr[HasProps, Locale, ResolvableLocale]:
    """
    Create an attribute containing a locale.
    """
    return OwnerAttr(LocaleDefinition(label=label, description=description)).setter(
        resolve_locale
    )


class HasLocale(Localized, LinkedDataDumpableWithSchemaJsonLdObject, HasProps):
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
        portable["locale"] = (
            to_language_tag(self.locale)
            if not isinstance(self, HasPrivacy) or self.public
            else None
        )
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("locale", OneOf(LocaleSchema(), Null()))
        return schema
