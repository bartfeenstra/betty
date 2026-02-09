"""
Dynamic content.
"""

from typing import Self

from typing_extensions import override

from betty.ancestry.has_links import HasLinks
from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import ProvidedTemplate, Template
from betty.document import Document
from betty.extension.wiki import Wiki
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.requirement.extension import require_extension
from betty.service.requirement.project import require_project


@ContentProviderDefinition("wiki-wikipedia-summary", label=_("Wikipedia summary"))
class WikipediaSummary(Template, Manufacturable):
    """
    A Wikipedia summary.

    .. plugin:: content-provider:wiki-wikipedia-summary
    """

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        await require_extension(Wiki, project)
        return cls(jinja=await project.jinja)

    @override
    async def provide_template(self, document: Document) -> ProvidedTemplate:
        if isinstance(document.resource, HasLinks):
            return "component/wiki/wikipedia-summary.html.j2", {
                "links": document.resource.links
            }
        return None
