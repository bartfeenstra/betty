"""
Tools for entities that have notes.
"""

from __future__ import annotations

from typing import Any

from betty.entity import Entity
from betty.entity.association import Associates, BidirectionalToManySingleType
from betty.locale.localizable.gettext import _
from betty.plugins.entity.note import Note


class HasNotes(Entity):
    """
    An entity that has notes associated with it.
    """

    notes = BidirectionalToManySingleType["HasNotes", Note](
        "betty.plugins.entity.note:Note",
        "entity",
        label=_("Notes"),
    )

    def __init__(
        self,
        *args: Any,
        notes: Associates[Note] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if notes is not None:
            self.notes = notes
