"""
Data types to describe information sources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks, Link
from betty.json.linked_data import dump_context
from betty.locale.localizable import (
    Localizable,
    OptionalStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    _,
    ngettext,
)
from betty.model import Entity, UserFacingEntity
from betty.model.association import (
    BidirectionalToMany,
    BidirectionalToZeroOrOne,
    ToManyAssociates,
    ToZeroOrOneAssociate,
)
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy, merge_privacies

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence

    from betty.ancestry.citation import Citation  # noqa F401
    from betty.ancestry.file_reference import FileReference
    from betty.ancestry.note import Note
    from betty.date import Datey
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
class Source(
    ShorthandPluginBase,
    HasDate,
    HasFileReferences,
    HasNotes,
    HasLinks,
    HasPrivacy,
    UserFacingEntity,
    Entity,
):
    """
    A source of information.
    """

    _plugin_id = "source"
    _plugin_label = _("Source")

    #: The source this one is directly contained by.
    contained_by = BidirectionalToZeroOrOne["Source", "Source"](
        "betty.ancestry.source:Source",
        "contained_by",
        "betty.ancestry.source:Source",
        "contains",
        title="Contained by",
        description="Another source this source may be contained by",
    )
    contains = BidirectionalToMany["Source", "Source"](
        "betty.ancestry.source:Source",
        "contains",
        "betty.ancestry.source:Source",
        "contained_by",
        title="Contains",
        description="Other sources this source may contain",
    )
    citations = BidirectionalToMany["Source", "Citation"](
        "betty.ancestry.source:Source",
        "citations",
        "betty.ancestry.citation:Citation",
        "source",
        title="Citations",
        description="The citations referencing this source",
    )

    #: The human-readable source name.
    name = OptionalStaticTranslationsLocalizableAttr("name", title="Name")

    #: The human-readable author.
    author = OptionalStaticTranslationsLocalizableAttr("author", title="Author")

    #: The human-readable publisher.
    publisher = OptionalStaticTranslationsLocalizableAttr(
        "publisher", title="Publisher"
    )

    def __init__(
        self,
        name: ShorthandStaticTranslations | None = None,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        author: ShorthandStaticTranslations | None = None,
        publisher: ShorthandStaticTranslations | None = None,
        contained_by: ToZeroOrOneAssociate[Source] = None,
        contains: ToManyAssociates[Source] | None = None,
        notes: ToManyAssociates[Note] | None = None,
        date: Datey | None = None,
        file_references: ToManyAssociates[FileReference] | None = None,
        links: MutableSequence[Link] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            notes=notes,
            date=date,
            file_references=file_references,
            links=links,
            privacy=privacy,
            public=public,
            private=private,
        )
        if name:
            self.name = name
        if author:
            self.author = author
        if publisher:
            self.publisher = publisher
        if contained_by is not None:
            self.contained_by = contained_by
        if contains is not None:
            self.contains = contains

    @override
    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.contained_by:
            return merge_privacies(privacy, self.contained_by)
        return privacy

    @property
    def walk_contains(self) -> Iterator[Source]:
        """
        All directly and indirectly contained sources.
        """
        for source in self.contains:
            yield source
            yield from source.contains

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Sources")

    @override
    @classmethod
    def plugin_label_count(cls, count: int) -> Localizable:
        return ngettext("{count} source", "{count} sources", count).format(
            count=str(count)
        )

    @override
    @property
    def label(self) -> Localizable:
        return self.name if self.name else super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        dump_context(dump, name="https://schema.org/name")
        return dump
