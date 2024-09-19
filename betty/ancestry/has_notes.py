"""
Data types for entities that have notes.
"""

from __future__ import annotations

from typing import Any, Iterable, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.note import Note
from betty.model import Entity, GeneratedEntityId, EntityReferenceCollectionSchema
from betty.model.association import OneToMany

if TYPE_CHECKING:
    from betty.json.schema import Object
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project


class HasNotes(Entity):
    """
    An entity that has notes associated with it.
    """

    notes = OneToMany["HasNotes", Note](
        "betty.ancestry.has_notes:HasNotes",
        "notes",
        "betty.ancestry.note:Note",
        "entity",
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
