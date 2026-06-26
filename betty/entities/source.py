"""
Data types to describe information sources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_file_references import HasFileReferences
from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.associations.to_many import ToMany, ToManyAssociates
from betty.associations.to_one import ToOne
from betty.attrs.date import HasAnyDate
from betty.attrs.localizable import new_localizable_attr
from betty.entity import EntityDefinition
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy
from betty.privacy.resolve import merge_privacies

if TYPE_CHECKING:
    from betty.association import Associate
    from betty.date import AnyDate
    from betty.entities.citation import Citation  # noqa: F401
    from betty.entities.file_reference import FileReference
    from betty.entities.link import Link
    from betty.entities.note import Note
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


@final
@EntityDefinition(
    "source",
    label=_("Source"),
    label_plural=_("Sources"),
    label_countable=ngettext("{count} source", "{count} sources"),
)
class Source(HasAnyDate, HasFileReferences, HasNotes, HasLinks):
    """
    .. plugin:: entity:source.
    """

    name = new_localizable_attr(
        label=_("Name"), linked_data_context="https://schema.org/name"
    ).optional
    """
    The source's name.
    """

    author = new_localizable_attr(label=_("Author")).optional
    """
    The source's author.
    """

    publisher = new_localizable_attr(label=_("Publisher")).optional
    """
    The source's publisher.
    """

    contained_by = ToOne[Self, "Source"](
        "betty.entities.source:Source",
        "contains",
        label=_("Contained by"),
        description=_("Another source this source may be contained by"),
    ).optional
    """
    Another source this source may be contained by
    """

    contains = ToMany[Self, "Source"](
        "betty.entities.source:Source",
        "contained_by",
        label=_("Contains"),
        description=_("Other sources this source may contain"),
    )
    """
    Other sources this source may contain
    """

    citations = ToMany[Self, "Citation"](
        "betty.entities.citation:Citation",
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
        id: ResolvableMachineName | None = None,  # noqa: A002
        author: ResolvableLocalizable | None = None,
        publisher: ResolvableLocalizable | None = None,
        contained_by: Associate[Self, Source] | None = None,
        contains: ToManyAssociates[Self, Source] = (),
        notes: ToManyAssociates[Self, Note] = (),
        date: AnyDate | None = None,
        files: ToManyAssociates[Self, FileReference] = (),
        links: ToManyAssociates[Self, Link] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(
            id=id,
            notes=notes,
            date=date,
            files=files,
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
