"""
Provide the Note entity type and utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.has_links import HasLinks
from betty.ancestry.media_type import HasMediaType
from betty.locale.localizable import (
    Localizable,
    StaticTranslations,
    _,
    ngettext,
)
from betty.model import EntityDefinition
from betty.model.association import BidirectionalToZeroOrOne, ToZeroOrOneAssociate
from betty.privacy import HasPrivacy, Privacy, is_public

if TYPE_CHECKING:
    from betty.ancestry.has_notes import HasNotes
    from betty.json.linked_data import JsonLdObject
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
@EntityDefinition(
    id="note",
    label=_("Note"),
    label_plural=_("Notes"),
    label_countable=ngettext("{count} note", "{count} notes"),
)
class Note(HasPrivacy, HasLinks, HasMediaType):
    """
    A note is a bit of textual information that can be associated with another entity.
    """

    #: The entity the note belongs to.
    entity = BidirectionalToZeroOrOne["Note", "HasNotes"](
        "betty.ancestry.note:Note",
        "entity",
        "betty.ancestry.has_notes:HasNotes",
        "notes",
        title="Entity",
        description="The entity the note belongs to",
    )

    def __init__(
        self,
        text: Localizable,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        entity: ToZeroOrOneAssociate[HasNotes] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            privacy=privacy,
            public=public,
            private=private,
        )
        self.text = text
        if entity is not None:
            self.entity = entity

    @override
    @property
    def label(self) -> Localizable:
        return self.text

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        if is_public(self):
            dump["text"] = await StaticTranslations.dump_linked_data_for(
                project, self.text
            )
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "text",
            await StaticTranslations.linked_data_schema(project),
            False,
        )
        return schema
