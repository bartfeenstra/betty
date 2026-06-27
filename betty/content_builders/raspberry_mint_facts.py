"""
The facts content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.entities.citation import Citation
from betty.entities.source import Source
from betty.factory import Manufacturable
from betty.functools import unique
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document
    from betty.entity import Entity


@final
@ContentBuilderDefinition(
    "raspberry-mint-facts",
    label=_("Facts"),
    description=_(
        "Other entities that reference a citation or source to back up their claims."
    ),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Facts(Template, Manufacturable):
    """
    A list of facts.

    .. plugin:: content-builder:raspberry-mint-facts
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        entities = []
        if isinstance(document.resource, Citation):
            entities.extend(document.resource.facts)
        if isinstance(document.resource, Source):
            entities.extend(unique(self._source_facts(document.resource)))
        if entities:
            return "entity/list.html.j2", {"entities": entities}
        return None

    def _source_facts(self, source: Source) -> Iterable[Entity]:
        for citation in source.citations:
            if citation.privacy.publishable:
                yield from citation.facts
        for contained in source.contains:
            yield from self._source_facts(contained)
