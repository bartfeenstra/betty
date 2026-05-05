"""
Provide the Note entity type and utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entity import EntityDefinition
from betty.entity.association import (
    BidirectionalToZeroOrOne,
    ToZeroOrOneAssociate,
)
from betty.entity.has_links import HasLinks
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.privacy import Privacy
from betty.privacy.resolve import is_public
from betty.properties.localizable import LocalizableProperty
from betty.properties.media_type import HasMediaType
from betty.properties.privacy import HasPrivacy

if TYPE_CHECKING:
    from betty.entity.has_notes import HasNotes
    from betty.linked_data import JsonLdObject
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "note",
    label=_("Note"),
    label_plural=_("Notes"),
    label_countable=ngettext("{count} note", "{count} notes"),
)
class Note(HasPrivacy, HasLinks, HasMediaType):
    """
    .. plugin:: entity:note.
    """

    text = LocalizableProperty(label=_("Text"))
    """
    The note text.
    """

    entity = BidirectionalToZeroOrOne["Note", "HasNotes"](
        "betty.entity.has_notes:HasNotes",
        "notes",
        label=_("Owner"),
        description=_("The entity the note belongs to"),
    )
    """
    The entity the note belongs to.
    """

    def __init__(
        self,
        text: ResolvableLocalizable,
        *,
        id: str | None = None,  # noqa: A002
        entity: ToZeroOrOneAssociate[HasNotes] | None = None,
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(id, privacy=privacy)
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
        if is_public(self):
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
