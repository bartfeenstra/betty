"""
Tools for entities that have links.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.entity import Entity
from betty.entity.association import BidirectionalToManySingleType, ToManyAssociates
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.entities.link import Link


class HasLinks(Entity):
    """
    An entity that has associated :py:class:`betty.entities.link.Link` entities.
    """

    links = BidirectionalToManySingleType["HasLinks", "Link"](
        "betty.entities.link:Link",
        "owner",
        label=_("Links"),
    )

    def __init__(self, *args: Any, links: ToManyAssociates[Link] = (), **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.links = links
