"""
Provide the Note entity type and utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.associations.to_one import ToOne
from betty.attrs.localizable import new_localizable_attr
from betty.attrs.media_type import HasMediaType
from betty.entity import EntityDefinition
from betty.json_schemas.static_translations import StaticTranslationsSchema
from betty.localizable.linked_data import dump_linked_data
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.association import Associate
    from betty.linked_data import JsonLdObject
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "note",
    label=_("Note"),
    label_plural=_("Notes"),
    label_countable=ngettext("{count} note", "{count} notes"),
)
class Note(HasLinks, HasMediaType):
    """
    .. plugin:: entity:note.
    """

    text = new_localizable_attr(label=_("Text"))
    """
    The note text.
    """

    entity = ToOne[Self, HasNotes](
        HasNotes,
        "notes",
        label=_("Owner"),
        description=_("The entity the note belongs to"),
    ).optional
    """
    The entity the note belongs to.
    """

    def __init__(
        self,
        text: ResolvableLocalizable,
        *,
        entity: Associate[Self, HasNotes] | None = None,
        id: ResolvableMachineName | None = None,  # noqa: A002
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(id=id, privacy=privacy)
        self.text = text
        if entity is not None:
            self.entity = entity

    @override
    @property
    def label(self) -> Localizable:
        return self.text

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        portable["@type"] = "https://schema.org/Thing"
        if self.public:
            portable["text"] = dump_linked_data(
                self.text, localizers=await project.public_localizers
            )
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "text",
            StaticTranslationsSchema(),
            False,
        )
        return schema
