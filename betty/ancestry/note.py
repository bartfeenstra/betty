"""
Provide the Note entity type and utilities.
"""

from __future__ import annotations

from typing import final, Any, Iterable, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.link import HasLinks
from betty.ancestry.privacy import HasPrivacy, Privacy
from betty.locale.localizable import (
    _,
    RequiredStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    Localizable,
    StaticTranslationsLocalizableSchema,
)
from betty.model import (
    UserFacingEntity,
    Entity,
    GeneratedEntityId,
    EntityReferenceCollectionSchema,
)
from betty.model.association import ManyToOne, OneToMany
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.json.schema import Object
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project


@final
class Note(ShorthandPluginBase, UserFacingEntity, HasPrivacy, HasLinks, Entity):
    """
    A note is a bit of textual information that can be associated with another entity.
    """

    _plugin_id = "note"
    _plugin_label = _("Note")

    #: The entity the note belongs to.
    entity = ManyToOne["Note", "HasNotes"](
        "betty.ancestry:Note", "entity", "betty.ancestry:HasNotes", "notes"
    )

    #: The human-readable note text.
    text = RequiredStaticTranslationsLocalizableAttr("text")

    def __init__(
        self,
        text: ShorthandStaticTranslations,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        entity: HasNotes & Entity | None = None,
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
    @property
    def label(self) -> Localizable:
        return self.text

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        if self.public:
            dump["text"] = await self.text.dump_linked_data(project)
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("text", StaticTranslationsLocalizableSchema(), False)
        return schema


class HasNotes(Entity):
    """
    An entity that has notes associated with it.
    """

    notes = OneToMany["HasNotes", Note](
        "betty.ancestry:HasNotes", "notes", "betty.ancestry:Note", "entity"
    )

    def __init__(
        self: HasNotes & Entity,
        *args: Any,
        notes: Iterable[Note] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if notes is not None:
            self.notes = notes

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["notes"] = [
            project.static_url_generator.generate(f"/note/{quote(note.id)}/index.json")
            for note in self.notes
            if not isinstance(note.id, GeneratedEntityId)
        ]
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("notes", EntityReferenceCollectionSchema(Note))
        return schema
