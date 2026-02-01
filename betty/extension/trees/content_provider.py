"""
Tree content.
"""

from typing import Self

from typing_extensions import override

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.extension.trees import Trees
from betty.locale.localizable.gettext import _
from betty.service.level.factory import ServiceLevelDependentSelfFactory
from betty.service.requirement import require_extension


@ContentProviderDefinition("trees-tree", label=_("Family tree"))
class Tree(Template, ServiceLevelDependentSelfFactory):
    """
    An interactive family tree.

    .. plugin:: content-provider:trees-tree
    """

    @override
    @classmethod
    @require_extension(Trees)
    async def new_for_services(cls, *, extension: Trees) -> Self:
        return cls(jinja2_environment=await extension._project.jinja2_environment)
