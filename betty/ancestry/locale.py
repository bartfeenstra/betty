"""
Data types that have a locale.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.json.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
)
from betty.json.schema import Null, OneOf
from betty.locale import LocaleLike, ensure_locale, to_language_tag
from betty.locale.localized import Localized
from betty.locale.schema import LocaleSchema
from betty.privacy import is_public

if TYPE_CHECKING:
    from babel import Locale

    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class HasLocale(Localized, LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    def __init__(
        self,
        *args: Any,
        locale: LocaleLike | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._locale = None if locale is None else ensure_locale(locale)

    @override  # type: ignore[explicit-override]
    @property
    def locale(self) -> Locale | None:
        return self._locale

    @locale.setter
    def locale(self, locale: Locale | None) -> None:
        self._locale = locale

    @override
    async def dump_linked_data(self, project: Project, /) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["locale"] = to_language_tag(self.locale) if is_public(self) else None
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("locale", OneOf(LocaleSchema(), Null()))
        return schema
