"""
Data types to describe information sources.
"""

from __future__ import annotations

from typing import final, Iterable, MutableSequence, Iterator, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.privacy import HasPrivacy, Privacy, merge_privacies
from betty.json.linked_data import dump_context
from betty.locale.localizable import (
    _,
    OptionalStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    Localizable,
    StaticTranslationsLocalizableSchema,
)
from betty.model import (
    UserFacingEntity,
    Entity,
    GeneratedEntityId,
    EntityReferenceCollectionSchema,
    EntityReferenceSchema,
)
from betty.model.association import (
    BidirectionalToZeroOrOne,
    BidirectionalToMany,
    ToOneResolver,
    ToManyResolver,
    ToZeroOrOneResolver,
)
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.ancestry.citation import Citation  # noqa F401
    from betty.ancestry.note import Note
    from betty.ancestry.file_reference import FileReference
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project
    from betty.json.schema import Object
    from betty.date import Datey


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
    )
    contains = BidirectionalToMany["Source", "Source"](
        "betty.ancestry.source:Source",
        "contains",
        "betty.ancestry.source:Source",
        "contained_by",
    )
    citations = BidirectionalToMany["Source", "Citation"](
        "betty.ancestry.source:Source",
        "citations",
        "betty.ancestry.citation:Citation",
        "source",
    )

    #: The human-readable source name.
    name = OptionalStaticTranslationsLocalizableAttr("name")

    #: The human-readable author.
    author = OptionalStaticTranslationsLocalizableAttr("author")

    #: The human-readable publisher.
    publisher = OptionalStaticTranslationsLocalizableAttr("publisher")

    def __init__(
        self,
        name: ShorthandStaticTranslations | None = None,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        author: ShorthandStaticTranslations | None = None,
        publisher: ShorthandStaticTranslations | None = None,
        contained_by: Source
        | ToZeroOrOneResolver[Source]
        | ToOneResolver[Source]
        | None = None,
        contains: Iterable[Source] | ToManyResolver[Source] | None = None,
        notes: Iterable[Note] | ToManyResolver[Note] | None = None,
        date: Datey | None = None,
        file_references: Iterable["FileReference"]
        | ToManyResolver["FileReference"]
        | None = None,
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
            return merge_privacies(privacy, self.contained_by.privacy)
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
    @property
    def label(self) -> Localizable:
        return self.name if self.name else super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        dump["contains"] = [
            project.static_url_generator.generate(
                f"/source/{quote(contained.id)}/index.json"
            )
            for contained in self.contains
            if not isinstance(contained.id, GeneratedEntityId)
        ]
        dump["citations"] = [
            project.static_url_generator.generate(
                f"/citation/{quote(citation.id)}/index.json"
            )
            for citation in self.citations
            if not isinstance(citation.id, GeneratedEntityId)
        ]
        if self.contained_by is not None and not isinstance(
            self.contained_by.id, GeneratedEntityId
        ):
            dump["containedBy"] = project.static_url_generator.generate(
                f"/source/{quote(self.contained_by.id)}/index.json"
            )
        if self.public:
            if self.name:
                dump_context(dump, name="https://schema.org/name")
                dump["name"] = await self.name.dump_linked_data(project)
            if self.author:
                dump["author"] = await self.author.dump_linked_data(project)
            if self.publisher:
                dump["publisher"] = await self.publisher.dump_linked_data(project)
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        from betty.ancestry.citation import Citation

        schema = await super().linked_data_schema(project)
        schema.add_property(
            "name", StaticTranslationsLocalizableSchema(title="Name"), False
        )
        schema.add_property(
            "author", StaticTranslationsLocalizableSchema(title="Author"), False
        )
        schema.add_property(
            "publisher", StaticTranslationsLocalizableSchema(title="Publisher"), False
        )
        schema.add_property("contains", EntityReferenceCollectionSchema(Source))
        schema.add_property("citations", EntityReferenceCollectionSchema(Citation))
        schema.add_property("containedBy", EntityReferenceSchema(Source), False)
        return schema
