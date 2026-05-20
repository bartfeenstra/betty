"""
Tools for entities that have file references.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from betty.associations.to_many import ToMany, ToManyAssociates
from betty.entity import Entity
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.entities.file_reference import FileReference


class HasFileReferences(Entity):
    """
    An entity that has associated :py:class:`betty.entities.file.File` entities.
    """

    files = ToMany[Self, "FileReference"](
        "betty.entities.file_reference:FileReference",
        "referee",
        label=_("File references"),
    )
    """
    References to files about this entity.
    """

    def __init__(
        self,
        *args: Any,
        files: ToManyAssociates[Self, FileReference] = (),
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.files = files
