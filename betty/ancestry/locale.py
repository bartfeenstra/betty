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
from betty.locale import UNDETERMINED_LOCALE, LocaleSchema
from betty.locale.localized import Localized
from betty.privacy import is_public

if TYPE_CHECKING:
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class HasLocale(Localized, LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    def __init__(
        self,
        *args: Any,
        locale: str = UNDETERMINED_LOCALE,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._locale = locale

    @override  # type: ignore[explicit-override]
    @property
    def locale(self) -> str:
        return self._locale

    @locale.setter
    def locale(self, locale: str) -> None:
        self._locale = locale

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["locale"] = self.locale if is_public(self) else None
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("locale", OneOf(LocaleSchema(), Null()))
        return schema
