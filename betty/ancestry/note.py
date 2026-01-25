"""
Provide the Note entity type and utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.has_links import HasLinks
from betty.ancestry.media_type import HasMediaType
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.property import LocalizableProperty
from betty.model import EntityDefinition
from betty.model.association import BidirectionalToZeroOrOne, ToZeroOrOneAssociate
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
    from betty.ancestry.has_notes import HasNotes
    from betty.locale.localizable import Localizable, LocalizableLike


@final
@EntityDefinition(
    "note",
    label=_("Note"),
    label_plural=_("Notes"),
    label_countable=ngettext("{count} note", "{count} notes"),
)
class Note(HasPrivacy, HasLinks, HasMediaType):
    """
    .. plugin:: entity:note.
    """

    text = LocalizableProperty(label=_("Text"))
    """
    The note text.
    """

    entity = BidirectionalToZeroOrOne["Note", "HasNotes"](
        "betty.ancestry.has_notes:HasNotes",
        "notes",
        label=_("Owner"),
        description=_("The entity the note belongs to"),
    )
    """
    The entity the note belongs to.
    """

    def __init__(
        self,
        text: LocalizableLike,
        *,
        id: str | None = None,  # noqa: A002
        entity: ToZeroOrOneAssociate[HasNotes] | None = None,
        privacy: Privacy | None = None,
    ):
        super().__init__(id, privacy=privacy)
        self.text = text
        if entity is not None:
            self.entity = entity

    @override
    @property
    def label(self) -> Localizable:
        return self.text
