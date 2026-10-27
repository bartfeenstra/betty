"""
Data types representing files on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.associations.has_citations import HasCitations
from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.associations.to_many import ToMany, ToManyAssociates
from betty.attrs.description import HasDescription
from betty.attrs.media_type import HasMediaType
from betty.attrs.path import new_path_attr
from betty.entities.file_reference import FileReference
from betty.entity import EntityDefinition
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.copyright_notice import CopyrightNotice
    from betty.entities.citation import Citation
    from betty.entities.link import Link
    from betty.entities.note import Note
    from betty.license import License
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.media_type import ResolvableMediaType
    from betty.pathlib import StrPath


@final
@EntityDefinition(
    "file",
    label=_("File"),
    label_plural=_("Files"),
    label_countable=ngettext("{count} file", "{count} files"),
)
class File(HasDescription, HasLinks, HasMediaType, HasNotes, HasCitations):
    """
    .. plugin:: entity:file.
    """

    referees = ToMany(
        FileReference,
        "file",
        label=_("Referees"),
        description=_("The entities referencing this file"),
    )
    """
    Other entities referencing this file.
    """

    copyright_notice: CopyrightNotice | None
    """
    The copyright notice for this file.
    """

    license: License | None
    """
    The license for this file.
    """

    path = new_path_attr()
    """
    The file's path on disk.
    """

    def __init__(
        self,
        path: StrPath,
        *,
        id: ResolvableMachineName | None = None,  # noqa: A002
        name: str | None = None,
        media_type: ResolvableMediaType | None = None,
        description: ResolvableLocalizable | None = None,
        notes: ToManyAssociates[Note] = (),
        citations: ToManyAssociates[Citation] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
        links: ToManyAssociates[Link] = (),
        copyright_notice: CopyrightNotice | None = None,
        license: License | None = None,  # noqa: A002
    ):
        super().__init__(
            id=id,
            media_type=media_type,
            description=description,
            notes=notes,
            citations=citations,
            privacy=privacy,
            links=links,
        )
        self.path = path
        self._name = name
        self.copyright_notice = copyright_notice
        self.license = license

    @property
    def name(self) -> str:
        """
        The file name.
        """
        return self._name or self.path.name

    @override
    @property
    def label(self) -> Localizable:
        return self.description or super().label
