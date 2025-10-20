"""
Data types to describe information sources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_links import HasLinks
from betty.ancestry.has_notes import HasNotes
from betty.json.linked_data import JsonLdObject, dump_context
from betty.locale.localizable import (
    Localizable,
    StaticTranslations,
    _,
    ngettext,
)
from betty.model import Entity, EntityDefinition
from betty.model.association import (
    BidirectionalToManySingleType,
    BidirectionalToZeroOrOne,
    ToManyAssociates,
    ToZeroOrOneAssociate,
)
from betty.privacy import HasPrivacy, Privacy, is_public, merge_privacies

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence

    from betty.ancestry.citation import Citation  # noqa F401
    from betty.ancestry.file_reference import FileReference
    from betty.ancestry.link import Link
    from betty.ancestry.note import Note
    from betty.date import DateLike
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
@EntityDefinition(
    id="source",
    label=_("Source"),
    label_plural=_("Sources"),
    label_countable=ngettext("{count} source", "{count} sources"),
)
class Source(HasDate, HasFileReferences, HasNotes, HasLinks, HasPrivacy, Entity):
    """
    A source of information.
    """

    #: The source this one is directly contained by.
    contained_by = BidirectionalToZeroOrOne["Source", "Source"](
        "betty.ancestry.source:Source",
        "contained_by",
        "betty.ancestry.source:Source",
        "contains",
        title="Contained by",
        description="Another source this source may be contained by",
    )
    contains = BidirectionalToManySingleType["Source", "Source"](
        "betty.ancestry.source:Source",
        "contains",
        "betty.ancestry.source:Source",
        "contained_by",
        title="Contains",
        description="Other sources this source may contain",
    )
    citations = BidirectionalToManySingleType["Source", "Citation"](
        "betty.ancestry.source:Source",
        "citations",
        "betty.ancestry.citation:Citation",
        "source",
        title="Citations",
        description="The citations referencing this source",
    )

    def __init__(
        self,
        name: Localizable | None = None,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        author: Localizable | None = None,
        publisher: Localizable | None = None,
        contained_by: ToZeroOrOneAssociate[Source] = None,
        contains: ToManyAssociates[Source] | None = None,
        notes: ToManyAssociates[Note] | None = None,
        date: DateLike | None = None,
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
        self.name = name
        self.author = author
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
    @property
    def label(self) -> Localizable:
        return self.name if self.name else super().label

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        static_translations_schema = await StaticTranslations.linked_data_schema(
            project
        )
        schema.add_property("author", static_translations_schema, False)
        schema.add_property("name", static_translations_schema, False)
        schema.add_property("publisher", static_translations_schema, False)
        return schema

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        dump_context(dump, name="https://schema.org/name")
        if is_public(self):
            if self.author is not None:
                dump["author"] = await StaticTranslations.dump_linked_data_for(
                    project, self.author
                )
            if self.name is not None:
                dump["name"] = await StaticTranslations.dump_linked_data_for(
                    project, self.name
                )
            if self.publisher is not None:
                dump["publisher"] = await StaticTranslations.dump_linked_data_for(
                    project, self.publisher
                )
        return dump
