"""
Tools for entities that have notes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from betty.associations.to_many import ToMany, ToManyAssociates
from betty.entity import Entity
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.entities.note import Note


class HasNotes(Entity):
    """
    An entity that has notes associated with it.
    """

    notes = ToMany[Self, "Note"](
        "betty.entities.note:Note",
        "entity",
        label=_("Notes"),
    )
    """
    Notes about this entity.
    """

    def __init__(
        self, *args: Any, notes: ToManyAssociates[Self, Note] = (), **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.notes = notes
