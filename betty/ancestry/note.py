"""
Provide the Note entity type and utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.link import HasLinks
from betty.locale.localizable import (
    Localizable,
    RequiredStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    _,
    ngettext,
)
from betty.model import Entity, UserFacingEntity
from betty.model.association import (
    BidirectionalToZeroOrOne,
    ToZeroOrOneAssociate,
)
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
    from betty.ancestry.has_notes import HasNotes
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
class Note(ShorthandPluginBase, UserFacingEntity, HasPrivacy, HasLinks, Entity):
    """
    A note is a bit of textual information that can be associated with another entity.
    """

    _plugin_id = "note"
    _plugin_label = _("Note")

    #: The entity the note belongs to.
    entity = BidirectionalToZeroOrOne["Note", "HasNotes"](
        "betty.ancestry.note:Note",
        "entity",
        "betty.ancestry.has_notes:HasNotes",
        "notes",
        title="Entity",
        description="The entity the note belongs to",
    )

    #: The human-readable note text.
    text = RequiredStaticTranslationsLocalizableAttr("text", title="Text")

    def __init__(
        self,
        text: ShorthandStaticTranslations,
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
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Notes")

    @override
    @classmethod
    def plugin_label_count(cls, count: int) -> Localizable:
        return ngettext("{count} note", "{count} notes", count).format(count=str(count))

    @override
    @property
    def label(self) -> Localizable:
        return self.text

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        return dump
