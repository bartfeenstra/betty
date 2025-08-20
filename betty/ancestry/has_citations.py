"""
Tools to build data types have citations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.model import Entity
from betty.model.association import BidirectionalToManySingleType, ToManyAssociates

if TYPE_CHECKING:
    from betty.ancestry.citation import Citation


class HasCitations(Entity):
    """
    An entity with citations that support it.
    """

    citations = BidirectionalToManySingleType["HasCitations", "Citation"](
        "betty.ancestry.has_citations:HasCitations",
        "citations",
        "betty.ancestry.citation:Citation",
        "facts",
        title="Citations",
        description="The citations backing up the claims made by this entity",
    )

    def __init__(
        self: HasCitations & Entity,
        *args: Any,
        citations: ToManyAssociates[Citation] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if citations is not None:
            self.citations = citations
