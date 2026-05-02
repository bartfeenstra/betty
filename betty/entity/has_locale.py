"""
Data types that have a locale.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.json_schema import Null, OneOf
from betty.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
)
from betty.locale import HasLocale as StdHasLocale
from betty.locale import to_language_tag
from betty.locale.schema import LocaleSchema
from betty.privacy import is_public

if TYPE_CHECKING:
    from babel import Locale

    from betty.portable import PortableMapping
    from betty.project import Project


class HasLocale(StdHasLocale, LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    @override
    @property
    def locale(self) -> Locale | None:
        return self._locale

    @locale.setter
    def locale(self, locale: Locale | None) -> None:
        self._locale = locale

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
