"""
Tools for entities that have file references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.entity import Entity
from betty.entity.association import BidirectionalToManySingleType, ToManyAssociates
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from betty.plugins.entity.file_reference import FileReference


class HasFileReferences(Entity):
    """
    An entity that has associated :py:class:`betty.plugins.entity.file.File` entities.
    """

    file_references = BidirectionalToManySingleType[
        "HasFileReferences", "FileReference"
    ](
        "betty.plugins.entity.file_reference:FileReference",
        "referee",
        label=_("File references"),
        linked_data_embedded=True,
    )

    def __init__(
        self,
        *args: Any,
        file_references: ToManyAssociates[FileReference] = (),
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.file_references = file_references
