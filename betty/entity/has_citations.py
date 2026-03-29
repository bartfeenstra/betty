"""
Tools for entities that have citations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.entity import Entity
from betty.entity.association import BidirectionalToManySingleType, ToManyAssociates
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from betty.plugins.entity.citation import Citation


class HasCitations(Entity):
    """
    An entity with citations that support it.
    """

    citations = BidirectionalToManySingleType["HasCitations", "Citation"](
        "betty.plugins.entity.citation:Citation",
        "facts",
        label=_("Citations"),
        description=_("The citations backing up the claims made by this entity"),
    )

    def __init__(
        self,
        *args: Any,
        citations: ToManyAssociates[Citation] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if citations is not None:
            self.citations = citations
