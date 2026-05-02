"""
Data types to describe information sources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entity import Entity, EntityDefinition
from betty.entity.association import (
    BidirectionalToManySingleType,
    BidirectionalToZeroOrOne,
    ToManyAssociates,
    ToZeroOrOneAssociate,
)
from betty.entity.has_date import HasDate
from betty.entity.has_file_references import HasFileReferences
from betty.entity.has_links import HasLinks
from betty.entity.has_notes import HasNotes
from betty.linked_data import JsonLdObject, dump_context
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.property import LocalizableProperty
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.privacy import HasPrivacy, Privacy, is_public, merge_privacies
from betty.property import Optional

if TYPE_CHECKING:
    from betty.date import ResolvableDate
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.plugins.entity.citation import Citation  # noqa: F401
    from betty.plugins.entity.file_reference import FileReference
    from betty.plugins.entity.link import Link
    from betty.plugins.entity.note import Note
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "source",
    label=_("Source"),
    label_plural=_("Sources"),
    label_countable=ngettext("{count} source", "{count} sources"),
    before=lambda other: other not in ("event", "person", "place"),
)
class Source(HasDate, HasFileReferences, HasNotes, HasLinks, HasPrivacy, Entity):
    """
    .. plugin:: entity:source.
    """

    name = Optional(LocalizableProperty(label=_("Name")))
    """
    The source's name.
    """

    author = Optional(LocalizableProperty(label=_("Author")))
    """
    The source's author.
    """

    publisher = Optional(LocalizableProperty(label=_("Publisher")))
    """
    The source's publisher.
    """

    contained_by = BidirectionalToZeroOrOne["Source", "Source"](
        "betty.plugins.entity.source:Source",
        "contains",
        label=_("Contained by"),
        description=_("Another source this source may be contained by"),
    )
    """
    Another source this source may be contained by
    """

    contains = BidirectionalToManySingleType["Source", "Source"](
        "betty.plugins.entity.source:Source",
        "contained_by",
        label=_("Contains"),
        description=_("Other sources this source may contain"),
    )
    """
    Other sources this source may contain
    """

    citations = BidirectionalToManySingleType["Source", "Citation"](
        "betty.plugins.entity.citation:Citation",
        "source",
        label=_("Citations"),
        description=_("The citations referencing this source"),
    )
    """
    The citations referencing this source
    """

    def __init__(
        self,
        name: ResolvableLocalizable | None = None,
        *,
        id: str | None = None,  # noqa: A002
        author: ResolvableLocalizable | None = None,
        publisher: ResolvableLocalizable | None = None,
        contained_by: ToZeroOrOneAssociate[Source] = None,
        contains: ToManyAssociates[Source] = (),
        notes: ToManyAssociates[Note] = (),
        date: ResolvableDate | None = None,
        file_references: ToManyAssociates[FileReference] = (),
        links: ToManyAssociates[Link] = (),
        privacy: Privacy | None = None,
    ):
        super().__init__(
            id,
            notes=notes,
            date=date,
            file_references=file_references,
            links=links,
            privacy=privacy,
        )
        self.name = name
        self.author = author
        self.publisher = publisher
        self.contained_by = contained_by
        self.contains = contains

    @override
    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.contained_by:
            return merge_privacies(privacy, self.contained_by)
        return privacy

    @override
    @property
    def label(self) -> Localizable:
        return self.name if self.name else super().label

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        static_translations_schema = StaticTranslationsSchema()
        schema.add_property("author", static_translations_schema, False)
        schema.add_property("name", static_translations_schema, False)
        schema.add_property("publisher", static_translations_schema, False)
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        portable["@type"] = "https://schema.org/Thing"
        dump_context(portable, name="https://schema.org/name")
        if is_public(self):
            public_localizers = await project.public_localizers
            if self.author is not None:
                portable["author"] = dump_linked_data(
                    self.author, localizers=public_localizers
                )
            if self.name is not None:
                portable["name"] = dump_linked_data(
                    self.name, localizers=public_localizers
                )
            if self.publisher is not None:
                portable["publisher"] = dump_linked_data(
                    self.publisher, localizers=public_localizers
                )
        return portable
