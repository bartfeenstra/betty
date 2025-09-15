"""
Tools to build data types that have links.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.model import Entity
from betty.model.association import BidirectionalToManySingleType, ToManyAssociates

if TYPE_CHECKING:
    from betty.ancestry.link import Link


class HasLinks(Entity):
    """
    An entity that has associated :py:class:`betty.ancestry.link.Link` entities.
    """

    links = BidirectionalToManySingleType["HasLinks & Entity", "Link"](
        "betty.ancestry.has_links:HasLinks",
        "links",
        "betty.ancestry.link:Link",
        "owner",
        title="Links",
        linked_data_embedded=True,
    )

    def __init__(
        self,
        *args: Any,
        links: ToManyAssociates[Link] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if links is not None:
            self.links = links
