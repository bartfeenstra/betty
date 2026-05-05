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
from betty.entity.has_file_references import HasFileReferences
from betty.entity.has_links import HasLinks
from betty.entity.has_notes import HasNotes
from betty.locale.localizable.gettext import _, ngettext
from betty.privacy import Privacy
from betty.privacy.resolve import merge_privacies
from betty.properties.date import HasAnyDate
from betty.properties.localizable import LocalizableProperty
from betty.properties.privacy import HasPrivacy
from betty.property import Optional

if TYPE_CHECKING:
    from betty.date import AnyDate
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.plugins.entity.citation import Citation  # noqa: F401
    from betty.plugins.entity.file_reference import FileReference
    from betty.plugins.entity.link import Link
    from betty.plugins.entity.note import Note


@final
@EntityDefinition(
    "source",
    label=_("Source"),
    label_plural=_("Sources"),
    label_countable=ngettext("{count} source", "{count} sources"),
)
class Source(HasAnyDate, HasFileReferences, HasNotes, HasLinks, HasPrivacy, Entity):
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
        date: AnyDate | None = None,
        file_references: ToManyAssociates[FileReference] = (),
        links: ToManyAssociates[Link] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
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
