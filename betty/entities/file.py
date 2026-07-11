"""
Data types representing files on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_citations import HasCitations
from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.associations.to_many import ToMany, ToManyAssociates
from betty.attrs.description import HasDescription
from betty.attrs.media_type import HasMediaType
from betty.attrs.path import new_path_attr
from betty.copyright_notice import CopyrightNoticeDefinition
from betty.entities.file_reference import FileReference
from betty.entity import EntityDefinition
from betty.json_schemas.plugin_id import new_plugin_id_schema
from betty.license import LicenseDefinition
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.copyright_notice import CopyrightNotice
    from betty.entities.citation import Citation
    from betty.entities.link import Link
    from betty.entities.note import Note
    from betty.license import License
    from betty.linked_data import LinkedData
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.media_type import ResolvableMediaType
    from betty.pathlib import StrPath
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidableType


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

    referees = ToMany[Self, FileReference](
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
        notes: ToManyAssociates[Self, Note] = (),
        citations: ToManyAssociates[Self, Citation] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
        links: ToManyAssociates[Self, Link] = (),
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

    @override
    @classmethod
    async def linked_data_schema(
        cls, project: Project, /
    ) -> VoidableType[PortableMapping]:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "copyrightNotice",
            new_plugin_id_schema(
                CopyrightNoticeDefinition.type(),
                [x async for x in project.plugins[CopyrightNoticeDefinition]],
            ),
            False,
        )
        schema.add_property(
            "license",
            new_plugin_id_schema(
                LicenseDefinition.type(),
                [x async for x in project.plugins[LicenseDefinition]],
            ),
            False,
        )
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> LinkedData:
        portable = await super().dump_linked_data(project)
        if self.copyright_notice:
            portable["copyrightNotice"] = self.copyright_notice.plugin().id
        if self.license:
            portable["license"] = self.license.plugin().id
        return portable
