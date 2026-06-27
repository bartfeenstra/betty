"""
Tools for entities that have links.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from betty.associations.to_many import ToMany, ToManyAssociates
from betty.entity import Entity
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.entities.link import Link


class HasLinks(Entity):
    """
    An entity that has associated :py:class:`betty.entities.link.Link` entities.
    """

    links = ToMany[Self, "Link"](
        "betty.entities.link:Link", "owner", label=_("Links"), privatize=True
    )
    """
    The links owned by this entity.
    """

    def __init__(
        self, *args: Any, links: ToManyAssociates[Self, Link] = (), **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.links = links
