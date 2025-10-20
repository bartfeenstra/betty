"""
Data types to reference files on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.ancestry.file import File
from betty.locale.localizable import _, ngettext
from betty.model import Entity, EntityDefinition
from betty.model.association import BidirectionalToOne, ToOneAssociate

if TYPE_CHECKING:
    from betty.ancestry.has_file_references import HasFileReferences
    from betty.image import FocusArea


@final
@EntityDefinition(
    id="file-reference",
    label=_("File reference"),
    label_plural=_("File references"),
    label_countable=ngettext("{count} file reference", "{count} file references"),
    public_facing=False,
)
class FileReference(Entity):
    """
    A reference between :py:class:`betty.ancestry.has_file_references.HasFileReferences` and betty.ancestry.file.File.

    This reference holds additional information specific to the relationship between the two entities.
    """

    #: The entity that references the file.
    referee = BidirectionalToOne["FileReference", "HasFileReferences"](
        "betty.ancestry.file_reference:FileReference",
        "referee",
        "betty.ancestry.has_file_references:HasFileReferences",
        "file_references",
        title="Referee",
        description="The entity referencing the file",
    )
    #: The referenced file.
    file = BidirectionalToOne["FileReference", File](
        "betty.ancestry.file_reference:FileReference",
        "file",
        "betty.ancestry.file:File",
        "referees",
        title="File",
        description="The file being referenced",
    )

    def __init__(
        self,
        referee: ToOneAssociate[HasFileReferences & Entity],
        file: ToOneAssociate[File],
        *,
        focus: FocusArea | None = None,
    ):
        super().__init__()
        self.referee = referee
        self.file = file
        self.focus = focus

    @property
    def focus(self) -> FocusArea | None:
        """
        The area within the 2-dimensional representation of the file to focus on.

        This can be used to locate where faces are in a photo, or a specific article in a newspaper scan, for example.
        """
        return self._focus

    @focus.setter
    def focus(self, focus: FocusArea | None) -> None:
        self._focus = focus
