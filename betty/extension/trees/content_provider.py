"""
Tree content.
"""

from typing import Self

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.extension.trees import Trees
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.requirement import HasRequirement, Requirement
from betty.service.level import ServiceLevel
from betty.service.level.factory import ServiceLevelDependentSelfFactory
from betty.service.requirement import require_project


@ContentProviderDefinition("trees-tree", label=_("Family tree"))
class Tree(Template, ServiceLevelDependentSelfFactory, HasRequirement):
    """
    An interactive family tree.
    """

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, *, project: Project) -> Self:
        return cls(jinja2_environment=await project.jinja2_environment)

    @override
    @classmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        return await Trees.requirement_for(
            services, cls.plugin().reference_label_with_type
        )
