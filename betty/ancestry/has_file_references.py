"""
Tools to build data types that reference files.
"""

from __future__ import annotations

from typing import Any, Iterable, TYPE_CHECKING

from betty.model import Entity
from betty.model.association import BidirectionalToMany, ToManyResolver

if TYPE_CHECKING:
    from betty.ancestry.file_reference import FileReference


class HasFileReferences(Entity):
    """
    An entity that has associated :py:class:`betty.ancestry.file.File` entities.
    """

    file_references = BidirectionalToMany[
        "HasFileReferences & Entity", "FileReference"
    ](
        "betty.ancestry.has_file_references:HasFileReferences",
        "file_references",
        "betty.ancestry.file_reference:FileReference",
        "referee",
        title="File references",
        linked_data_embedded=True,
    )

    def __init__(
        self,
        *args: Any,
        file_references: Iterable[FileReference]
        | ToManyResolver[FileReference]
        | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if file_references is not None:
            self.file_references = file_references
