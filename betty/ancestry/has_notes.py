"""
Data types for entities that have notes.
"""

from __future__ import annotations

from typing import Any

from betty.ancestry.note import Note
from betty.locale.localizable.gettext import _
from betty.model import Entity
from betty.model.association import BidirectionalToManySingleType, ToManyAssociates


class HasNotes(Entity):
    """
    An entity that has notes associated with it.
    """

    notes = BidirectionalToManySingleType["HasNotes", Note](
        "betty.ancestry.note:Note",
        "entity",
        label=_("Notes"),
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
