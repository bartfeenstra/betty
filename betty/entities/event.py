"""
Data types to describe events.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.associations.has_citations import HasCitations
from betty.associations.has_file_references import HasFileReferences
from betty.associations.has_links import HasLinks
from betty.associations.has_notes import HasNotes
from betty.associations.to_many import ToMany, ToManyAssociates
from betty.associations.to_one import ToOne
from betty.attrs.date import HasAnyDate
from betty.attrs.description import HasDescription
from betty.attrs.localizable import new_localizable_attr
from betty.entities.place import Place
from betty.entities.presence import Presence
from betty.entity import EntityDefinition
from betty.event_types.unknown import UnknownEventType
from betty.localizables.gettext import _, ngettext
from betty.localizables.markup import JoinAnd
from betty.privacy import Privacy
from betty.roles.subject import Subject

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.association import Associate
    from betty.date import AnyDate
    from betty.entities.citation import Citation
    from betty.entities.file_reference import FileReference
    from betty.entities.note import Note
    from betty.event_type import EventType
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


@final
@EntityDefinition(
    "event",
    label=_("Event"),
    label_plural=_("Events"),
    label_countable=ngettext("{count} event", "{count} events"),
)
class Event(
    HasAnyDate, HasFileReferences, HasCitations, HasNotes, HasDescription, HasLinks
):
    """
    .. plugin:: entity:event.
    """

    name = new_localizable_attr(label=_("Name")).optional
    """
    The event's name, if it has any.
    """

    place = ToOne(
        Place, "events", label=_("Place"), description=_("The location of the event")
    ).optional
    """
    The place the event happened.
    """
    presences = ToMany(
        Presence,
        "event",
        label=_("Presences"),
        description=_("People's presences at this event"),
    )
    """
    People's presences at this event.
    """

    def __init__(
        self,
        *,
        id: ResolvableMachineName | None = None,  # noqa: A002
        event_type: EventType | None = None,
        date: AnyDate | None = None,
        files: ToManyAssociates[FileReference] = (),
        citations: ToManyAssociates[Citation] = (),
        notes: ToManyAssociates[Note] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
        place: Associate[Place] | None = None,
        description: ResolvableLocalizable | None = None,
        presences: ToManyAssociates[Presence] = (),
        name: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            id=id,
            date=date,
            files=files,
            citations=citations,
            notes=notes,
            privacy=privacy,
            description=description,
        )
        self.event_type = event_type or UnknownEventType()
        """
        The type of event.
        """
        self.place = place
        self.presences = presences
        self.name = name

    @override
    @property
    def label(self) -> Localizable:
        if self.name:
            return self.name

        format_kwargs: Mapping[str, ResolvableLocalizable] = {
            "event_type": self.event_type.definition.label,
        }
        subjects = [
            presence.person
            for presence in self.presences
            if presence.public
            and isinstance(presence.role, Subject)
            and presence.person.public
        ]
        if subjects:
            format_kwargs["subjects"] = JoinAnd(*(person.label for person in subjects))

        if subjects:
            return _("{event_type} of {subjects}").format(**format_kwargs)
        return _("{event_type}").format(**format_kwargs)
