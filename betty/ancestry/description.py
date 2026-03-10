"""
Data types with human-readable description texts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.json.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
    dump_context,
)
from betty.locale.localizable.gettext import _
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.property import LocalizableProperty
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.privacy import is_public
from betty.property import Optional

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


class HasDescription(LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource with a description.
    """

    description = Optional(LocalizableProperty(label=_("Description")))
    """
    The description.
    """

    def __init__(
        self,
        *args: Any,
        description: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.description = description

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "description",
            StaticTranslationsSchema(),
            False,
        )
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        linked_data = dict(await super().dump_linked_data(project))
        dump_context(linked_data, description="https://schema.org/description")
        if self.description is not None and is_public(self):
            linked_data["description"] = dump_linked_data(
                self.description, localizers=await project.public_localizers
            )
        return linked_data
