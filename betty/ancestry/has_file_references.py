"""
Tools to build data types that reference files.
"""

from __future__ import annotations

from typing import Any, Iterable, TYPE_CHECKING


from betty.model import Entity
from betty.model.association import OneToMany

if TYPE_CHECKING:
    from betty.ancestry import FileReference


class HasFileReferences(Entity):
    """
    An entity that has associated :py:class:`betty.ancestry.File` entities.
    """

    file_references = OneToMany["HasFileReferences & Entity", "FileReference"](
        "betty.ancestry:HasFileReferences",
        "file_references",
        "betty.ancestry:FileReference",
        "referee",
    )

    def __init__(
        self: HasFileReferences & Entity,
        *args: Any,
        file_references: Iterable[FileReference] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if file_references is not None:
            self.file_references = file_references
