"""
Data types representing files on disk.
"""

from __future__ import annotations

from typing import final, Iterable, MutableSequence, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.description import HasDescription
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.media_type import HasMediaType
from betty.json.schema import Enum
from betty.locale.localizable import _, ShorthandStaticTranslations, Localizable
from betty.model import UserFacingEntity, Entity
from betty.model.association import BidirectionalToMany, ToManyResolver
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
    from betty.json.linked_data import JsonLdObject
    from betty.project import Project
    from betty.serde.dump import DumpMapping, Dump
    from betty.copyright_notice import CopyrightNotice
    from betty.license import License
    from betty.ancestry.citation import Citation
    from betty.ancestry.note import Note
    from betty.ancestry.file_reference import FileReference  # noqa F401
    from betty.media_type import MediaType
    from pathlib import Path


@final
class File(
    ShorthandPluginBase,
    HasDescription,
    HasPrivacy,
    HasLinks,
    HasMediaType,
    HasNotes,
    HasCitations,
    UserFacingEntity,
    Entity,
):
    """
    A file on disk.

    This includes but is not limited to:

    - images
    - video
    - audio
    - PDF documents
    """

    _plugin_id = "file"
    _plugin_label = _("File")

    referees = BidirectionalToMany["File", "FileReference"](
        "betty.ancestry.file:File",
        "referees",
        "betty.ancestry.file_reference:FileReference",
        "file",
        title="Referees",
        description="The entities referencing this file",
        linked_data_embedded=True,
    )

    #: The copyright notice for this file.
    copyright_notice: CopyrightNotice | None

    #: The license for this file.
    license: License | None

    def __init__(
        self,
        path: Path,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        name: str | None = None,
        media_type: MediaType | None = None,
        description: ShorthandStaticTranslations | None = None,
        notes: Iterable[Note] | ToManyResolver[Note] | None = None,
        citations: Iterable[Citation] | ToManyResolver[Citation] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        links: MutableSequence[Link] | None = None,
        copyright_notice: CopyrightNotice | None = None,
        license: License | None = None,  # noqa A002
    ):
        super().__init__(
            id,
            media_type=media_type,
            description=description,
            notes=notes,
            citations=citations,
            privacy=privacy,
            public=public,
            private=private,
            links=links,
        )
        self._path = path
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
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Files")

    @property
    def path(self) -> Path:
        """
        The file's path on disk.
        """
        return self._path

    @override
    @property
    def label(self) -> Localizable:
        return self.description or super().label

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "copyrightNotice",
            Enum(
                *[
                    plugin.plugin_id()
                    async for plugin in project.copyright_notice_repository
                ],  # noqa A002
                title="Copyright notice",
                description="A copyright notice plugin ID",
            ),
            False,
        )
        schema.add_property(
            "license",
            Enum(
                *[
                    plugin.plugin_id()
                    async for plugin in await project.license_repository
                ],  # noqa A002
                title="License",
                description="A license plugin ID",
            ),
            False,
        )
        return schema

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.copyright_notice:
            dump["copyrightNotice"] = self.copyright_notice.plugin_id()
        if self.license:
            dump["license"] = self.license.plugin_id()
        return dump
