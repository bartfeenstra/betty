"""
Data types to reference files on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.file import File
from betty.locale.localizable import _, Localizable
from betty.model import Entity
from betty.model.association import BidirectionalToOne, ToOneResolver
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.image import FocusArea
    from betty.ancestry.has_file_references import HasFileReferences


class FileReference(ShorthandPluginBase, Entity):
    """
    A reference between :py:class:`betty.ancestry.has_file_references.HasFileReferences` and betty.ancestry.file.File.

    This reference holds additional information specific to the relationship between the two entities.
    """

    _plugin_id = "file-reference"
    _plugin_label = _("File reference")

    #: The entity that references the file.
    referee = BidirectionalToOne["FileReference", "HasFileReferences"](
        "betty.ancestry.file_reference:FileReference",
        "referee",
        "betty.ancestry.has_file_references:HasFileReferences",
        "file_references",
    )
    #: The referenced file.
    file = BidirectionalToOne["FileReference", File](
        "betty.ancestry.file_reference:FileReference",
        "file",
        "betty.ancestry.file:File",
        "referees",
    )

    def __init__(
        self,
        referee: HasFileReferences & Entity | ToOneResolver[HasFileReferences & Entity],
        file: File | ToOneResolver[File],
        focus: FocusArea | None = None,
    ):
        super().__init__()
        self.referee = referee
        self.file = file
        self.focus = focus

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("File references")

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
