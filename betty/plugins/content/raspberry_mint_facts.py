"""
The facts content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.functools import unique
from betty.locale.localizable.gettext import _
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.citation import Citation
from betty.plugins.entity.source import Source
from betty.privacy import is_public
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document
    from betty.model import Entity
    from betty.project import Project


@final
@ContentDefinition(
    "raspberry-mint-facts",
    label=_("Facts"),
    description=_(
        "Other entities that reference a citation or source to back up their claims."
    ),
)
class Facts(Template, Manufacturable):
    """
    A list of facts.

    .. plugin:: content:raspberry-mint-facts
    """

    @override
    @classmethod
    @require_project
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
        for citation in filter(is_public, source.citations):
            yield from citation.facts
        for contained in source.contains:
            yield from self._source_facts(contained)
