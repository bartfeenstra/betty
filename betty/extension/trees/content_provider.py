"""
Tree content.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Self

from typing_extensions import override

from betty.ancestry.person import Person
from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.document import Document
from betty.extension.trees import Trees
from betty.locale.localizable.gettext import _
from betty.service.level import Manufacturable
from betty.service.requirement.extension import require_extension


@ContentProviderDefinition("trees-tree", label=_("Family tree"))
class Tree(Template, Manufacturable):
    """
    An interactive family tree.

    .. plugin:: content-provider:trees-tree
    """

    @override
    @classmethod
    @require_extension(Trees)
    async def new_for_services(cls, *, extension: Trees) -> Self:
        return cls(jinja=await extension.services.jinja)

    @override
    async def provide_template(
        self, document: Document
    ) -> str | Iterable[str] | tuple[str | Iterable[str], Mapping[str, Any]] | None:
        if isinstance(document.resource, Person):
            return "component/trees/tree.html.j2", {
                "person": document.resource,
            }
        return None
