"""
Data types to reference files on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.entities.file import File
from betty.entity import Entity, EntityDefinition
from betty.entity.association import (
    BidirectionalToOne,
    ToOneAssociate,
)
from betty.locale.localizable.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.entity.has_file_references import HasFileReferences
    from betty.image import FocusArea


@final
@EntityDefinition(
    "file-reference",
    label=_("File reference"),
    label_plural=_("File references"),
    label_countable=ngettext("{count} file reference", "{count} file references"),
    public_facing=False,
)
class FileReference(Entity):
    """
    .. plugin:: entity:file-reference.
    """

    referee = BidirectionalToOne["FileReference", "HasFileReferences"](
        "betty.entity.has_file_references:HasFileReferences",
        "file_references",
        label=_("Referee"),
        description=_("The entity referencing the file"),
    )
    """
    The entity that references the file.
    """

    file = BidirectionalToOne["FileReference", File](
        "betty.entities.file:File",
        "referees",
        label=_("File"),
        description=_("The file being referenced"),
    )
    """
    The referenced file.
    """

    def __init__(
        self,
        referee: ToOneAssociate[HasFileReferences],
        file: ToOneAssociate[File],
        *,
        focus: FocusArea | None = None,
    ):
        super().__init__()
        self.referee = referee
        self.file = file
        self.focus = focus
        """
        The area within the 2-dimensional representation of the file to focus on.

        This can be used to locate where faces are in a photo, or a specific article in a newspaper scan, for example.
        """
