"""
Provide the Note entity type and utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entity import EntityDefinition
from betty.entity.association import (
    BidirectionalToZeroOrOne,
    ToZeroOrOneAssociate,
)
from betty.entity.has_links import HasLinks
from betty.locale.localizable.gettext import _, ngettext
from betty.privacy import Privacy
from betty.properties.localizable import LocalizableProperty
from betty.properties.media_type import HasMediaType
from betty.properties.privacy import HasPrivacy

if TYPE_CHECKING:
    from betty.entity.has_notes import HasNotes
    from betty.locale.localizable import Localizable, ResolvableLocalizable


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
        "betty.entity.has_notes:HasNotes",
        "notes",
        label=_("Owner"),
        description=_("The entity the note belongs to"),
    )
    """
    The entity the note belongs to.
    """

    def __init__(
        self,
        text: ResolvableLocalizable,
        *,
        id: str | None = None,  # noqa: A002
        entity: ToZeroOrOneAssociate[HasNotes] | None = None,
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(id, privacy=privacy)
        self.text = text
        if entity is not None:
            self.entity = entity

    @override
    @property
    def label(self) -> Localizable:
        return self.text
