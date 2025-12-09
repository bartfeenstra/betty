"""
Tree content.
"""

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable.gettext import _
from betty.project.extension.trees import Trees
from betty.requirement import HasRequirement, Requirement
from betty.service.level import ServiceLevel


@ContentProviderDefinition("trees-tree", label=_("Family tree"))
class Tree(Template, HasRequirement):
    """
    An interactive family tree.
    """

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Trees.requirement_for(
            services, cls.plugin().reference_label_with_type
        )
