"""
Dynamic content.
"""

from typing import Self, override

from betty.ancestry.has_links import HasLinks
from betty.content import ContentDefinition
from betty.content.contents import Template, TemplateBuild
from betty.document import Document
from betty.extension.wiki import Wiki
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.extension import require_extension
from betty.service.requirement.project import require_project


@ContentDefinition("wiki-wikipedia-summary", label=_("Wikipedia summary"))
class WikipediaSummary(Template, Manufacturable):
    """
    A Wikipedia summary.

    .. plugin:: content:wiki-wikipedia-summary
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        await require_extension(Wiki, project)
        return cls(jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasLinks):
            return "component/wiki/wikipedia-summary.html.j2", {
                "links": document.resource.links
            }
        return None
