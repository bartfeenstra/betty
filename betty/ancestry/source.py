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
from betty.data.aggregate.record.object.property import Optional
from betty.json.linked_data import dump_context
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.property import LocalizableProperty
from betty.model import Entity, EntityDefinition
from betty.model.association import (
    BidirectionalToManySingleType,
    BidirectionalToZeroOrOne,
    ToManyAssociates,
    ToZeroOrOneAssociate,
)
from betty.privacy import HasPrivacy, Privacy, merge_privacies

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence

    from betty.ancestry.citation import Citation  # noqa: F401
    from betty.ancestry.file_reference import FileReference
    from betty.ancestry.link import Link
    from betty.ancestry.note import Note
    from betty.date import DateLike
    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "source",
    label=_("Source"),
    label_plural=_("Sources"),
    label_countable=ngettext("{count} source", "{count} sources"),
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
        "betty.ancestry.source:Source",
        "contains",
        label=_("Contained by"),
        description=_("Another source this source may be contained by"),
    )
    """
    Another source this source may be contained by
    """

    contains = BidirectionalToManySingleType["Source", "Source"](
        "betty.ancestry.source:Source",
        "contained_by",
        label=_("Contains"),
        description=_("Other sources this source may contain"),
    )
    """
    Other sources this source may contain
    """

    citations = BidirectionalToManySingleType["Source", "Citation"](
        "betty.ancestry.citation:Citation",
        "source",
        label=_("Citations"),
        description=_("The citations referencing this source"),
    )
    """
    The citations referencing this source
    """

    def __init__(
        self,
        name: LocalizableLike | None = None,
        *,
        id: str | None = None,  # noqa: A002
        author: LocalizableLike | None = None,
        publisher: LocalizableLike | None = None,
        contained_by: ToZeroOrOneAssociate[Source] = None,
        contains: ToManyAssociates[Source] | None = None,
        notes: ToManyAssociates[Note] | None = None,
        date: DateLike | None = None,
        file_references: ToManyAssociates[FileReference] | None = None,
        links: MutableSequence[Link] | None = None,
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
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable = await super().dump_linked_data(project)
        dump_context(portable, name="https://schema.org/name")
        return portable
