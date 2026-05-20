"""
Tools for entities that have citations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from betty.associations.to_many import ToMany, ToManyAssociates
from betty.entity import Entity
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.entities.citation import Citation


class HasCitations(Entity):
    """
    An entity with citations that support it.
    """

    citations = ToMany[Self, "Citation"](
        "betty.entities.citation:Citation",
        "facts",
        label=_("Citations"),
        description=_("The citations backing up the claims made by this entity"),
    )
    """
    The citations backing up the claims made by this entity.
    """

    def __init__(
        self,
        *args: Any,
        citations: ToManyAssociates[Self, Citation] = (),
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.citations = citations
