"""
Data types for entities that have notes.
"""

from __future__ import annotations

from typing import Any, Iterable

from betty.ancestry.note import Note
from betty.model import Entity
from betty.model.association import BidirectionalToMany, ToManyResolver


class HasNotes(Entity):
    """
    An entity that has notes associated with it.
    """

    notes = BidirectionalToMany["HasNotes", Note](
        "betty.ancestry.has_notes:HasNotes",
        "notes",
        "betty.ancestry.note:Note",
        "entity",
        title="Notes",
    )

    def __init__(
        self,
        *args: Any,
        notes: Iterable[Note] | ToManyResolver[Note] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if notes is not None:
            self.notes = notes
