"""
Provide the Note entity type and utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.associations.to_one import ToOne
from betty.attrs.localizable import new_localizable_attr
from betty.attrs.media_type import HasMediaType
from betty.entity import EntityDefinition
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.association import Associate
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


@final
@EntityDefinition(
    "note",
    label=_("Note"),
    label_plural=_("Notes"),
    label_countable=ngettext("{count} note", "{count} notes"),
)
class Note(HasLinks, HasMediaType):
    """
    .. plugin:: entity:note.
    """

    text = new_localizable_attr(label=_("Text"))
    """
    The note text.
    """

    entity = ToOne[Self, HasNotes](
        HasNotes,
        "notes",
        label=_("Owner"),
        description=_("The entity the note belongs to"),
    ).optional
    """
    The entity the note belongs to.
    """

    def __init__(
        self,
        text: ResolvableLocalizable,
        *,
        entity: Associate[Self, HasNotes] | None = None,
        id: ResolvableMachineName | None = None,  # noqa: A002
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(id=id, privacy=privacy)
        self.text = text
        if entity is not None:
            self.entity = entity

    @override
    @property
    def label(self) -> Localizable:
        return self.text
