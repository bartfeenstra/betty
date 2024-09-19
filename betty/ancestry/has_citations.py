"""
Tools to build data types have citations.
"""

from __future__ import annotations

from typing import Any, Iterable, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty.model import Entity, GeneratedEntityId, EntityReferenceCollectionSchema
from betty.model.association import ManyToMany

if TYPE_CHECKING:
    from betty.ancestry import Citation
    from betty.json.schema import Object
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project


class HasCitations(Entity):
    """
    An entity with citations that support it.
    """

    citations = ManyToMany["HasCitations & Entity", "Citation"](
        "betty.ancestry.has_citations:HasCitations",
        "citations",
        "betty.ancestry:Citation",
        "facts",
    )

    def __init__(
        self: HasCitations & Entity,
        *args: Any,
        citations: Iterable[Citation] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if citations is not None:
            self.citations = citations

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["citations"] = [
            project.static_url_generator.generate(
                f"/citation/{quote(citation.id)}/index.json"
            )
            for citation in self.citations
            if not isinstance(citation.id, GeneratedEntityId)
        ]
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        from betty.ancestry import Citation

        schema = await super().linked_data_schema(project)
        schema.add_property("citations", EntityReferenceCollectionSchema(Citation))
        return schema
