"""
Data types to reference files on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final

from betty.associations.has_file_references import HasFileReferences
from betty.associations.to_one import ToOne, ToOneAssociate
from betty.entity import Entity, EntityDefinition
from betty.localizables.gettext import _, ngettext

if TYPE_CHECKING:
    from betty.entities.file import File
    from betty.image import FocusArea
    from betty.machine_name import ResolvableMachineName


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

    referee = ToOne[Self, HasFileReferences](
        HasFileReferences,
        "files",
        label=_("Referee"),
        description=_("The entity referencing the file"),
    )
    """
    The entity that references the file.
    """

    file = ToOne[Self, "File"](
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
        referee: ToOneAssociate[Self, HasFileReferences],
        file: ToOneAssociate[Self, File],
        *,
        id: ResolvableMachineName | None = None,  # noqa: A002
        focus: FocusArea | None = None,
    ):
        super().__init__(id=id)
        self.referee = referee
        self.file = file
        self.focus = focus
        """
        The area within the 2-dimensional representation of the file to focus on.

        This can be used to locate where faces are in a photo, or a specific article in a newspaper scan, for example.
        """
