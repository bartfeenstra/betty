"""
Data types for entities that have notes.
"""

from __future__ import annotations

from typing import Any

from betty.ancestry.note import Note
from betty.model import Entity
from betty.model.association import BidirectionalToManySingleType, ToManyAssociates


class HasNotes(Entity):
    """
    An entity that has notes associated with it.
    """

    notes = BidirectionalToManySingleType["HasNotes", Note](
        "betty.ancestry.has_notes:HasNotes",
        "notes",
        "betty.ancestry.note:Note",
        "entity",
        title="Notes",
    )

    def __init__(
        self,
        *args: Any,
        notes: ToManyAssociates[Note] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if notes is not None:
            self.notes = notes
