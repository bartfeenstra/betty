"""
Data types representing files on disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.description import HasDescription
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.media_type import HasMediaType
from betty.locale.localizable import (
    Localizable,
    ShorthandStaticTranslations,
    _,
    ngettext,
)
from betty.model import Entity, UserFacingEntity
from betty.model.association import (
    BidirectionalToMany,
    ToManyAssociates,
)
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableSequence
    from pathlib import Path

    from betty.ancestry.citation import Citation
    from betty.ancestry.file_reference import FileReference  # noqa F401
    from betty.ancestry.note import Note
    from betty.copyright_notice import CopyrightNotice
    from betty.json.linked_data import JsonLdObject
    from betty.license import License
    from betty.media_type import MediaType
    from betty.mutability import Mutable
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


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
        notes: ToManyAssociates[Note] | None = None,
        citations: ToManyAssociates[Citation] | None = None,
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

    @override
    def get_mutable_instances(self) -> Iterable[Mutable]:
        if self.copyright_notice is not None:
            yield self.copyright_notice
        if self.license is not None:
            yield self.license

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

    @override
    @classmethod
    def plugin_label_count(cls, count: int) -> Localizable:
        return ngettext("{count} file", "{count} files", count).format(count=str(count))

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
            await project.copyright_notice_repository.plugin_id_schema,
            False,
        )
        schema.add_property(
            "license", await (await project.license_repository).plugin_id_schema, False
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
