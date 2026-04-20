"""
Tools for entities that have links.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.entity import Entity
from betty.entity.association import BidirectionalToManySingleType, ToManyAssociates
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from betty.plugins.entity.link import Link


class HasLinks(Entity):
    """
    An entity that has associated :py:class:`betty.plugins.entity.link.Link` entities.
    """

    links = BidirectionalToManySingleType["HasLinks", "Link"](
        "betty.plugins.entity.link:Link",
        "owner",
        label=_("Links"),
        linked_data_embedded=True,
    )

    def __init__(self, *args: Any, links: ToManyAssociates[Link] = (), **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.links = links
