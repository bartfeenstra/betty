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
from betty.locale.localizable import _, ShorthandStaticTranslations, Localizable
from betty.model import UserFacingEntity, Entity
from betty.model.association import BidirectionalToMany, ToManyResolver
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
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
