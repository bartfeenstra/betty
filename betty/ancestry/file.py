"""
Data types representing files on disk.
"""

from __future__ import annotations

from typing import final, Iterable, MutableSequence, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.description import HasDescription
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.media_type import HasMediaType
from betty.ancestry.privacy import HasPrivacy, Privacy
from betty.json.schema import Object, Array, String
from betty.locale.localizable import _, ShorthandStaticTranslations, Localizable
from betty.model import UserFacingEntity, Entity, GeneratedEntityId
from betty.model.association import BidirectionalToMany, ToManyResolver
from betty.plugin import ShorthandPluginBase
from betty.string import camel_case_to_kebab_case

if TYPE_CHECKING:
    from betty.ancestry.citation import Citation
    from betty.ancestry.note import Note
    from betty.ancestry.file_reference import FileReference  # noqa F401
    from betty.media_type import MediaType
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project
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
    )

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
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["entities"] = [
            project.static_url_generator.generate(
                f"/{camel_case_to_kebab_case(file_reference.referee.plugin_id())}/{quote(file_reference.referee.id)}/index.json"
            )
            for file_reference in self.referees
            if not isinstance(file_reference.referee.id, GeneratedEntityId)
        ]
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "entities",
            Array(
                String(format=String.Format.URI),
                title="Entities",
                description="The entities this file is associated with",
            ),
        )
        return schema
