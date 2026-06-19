"""
Data that has human-readable descriptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attrs.localizable import new_localizable_attr
from betty.attrs.privacy import HasPrivacy
from betty.json_schemas.static_translations import StaticTranslationsSchema
from betty.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
    dump_context,
)
from betty.locale.localizable.gettext import _
from betty.locale.localizable.linked_data import dump_linked_data
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


class HasDescription(LinkedDataDumpableWithSchemaJsonLdObject, HasProps):
    """
    Data with a description.
    """

    description = new_localizable_attr(label=_("Description")).optional
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
        portable = await super().dump_linked_data(project)
        dump_context(portable, description="https://schema.org/description")
        if self.description is not None and (
            not isinstance(self, HasPrivacy) or self.public
        ):
            portable["description"] = dump_linked_data(
                self.description, localizers=await project.public_localizers
            )
        return portable
