"""
Tree content.
"""

from betty.content_provider import ContentProviderDefinition
from betty.content_provider.content_providers import Template
from betty.locale.localizable import _


@ContentProviderDefinition(
    id="trees-tree",
    label=_("Family tree"),
)
class Tree(Template):
    """
    An interactive family tree.
    """
