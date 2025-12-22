"""
Data types to describe events.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.description import HasDescription
from betty.ancestry.event_type import EventTypeDefinition
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_links import HasLinks
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.place import Place
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.json.linked_data import JsonLdObject, dump_context
from betty.json.schema import String
from betty.locale.localizable.attr import OptionalLocalizableAttr
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.markup import AllEnumeration
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.model import EntityDefinition
from betty.model.association import (
    BidirectionalToManySingleType,
    BidirectionalToZeroOrOne,
    ToManyAssociates,
    ToZeroOrOneAssociate,
)
from betty.plugin.schema import PluginIdSchema
from betty.privacy import HasPrivacy, Privacy

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from betty.ancestry.citation import Citation
    from betty.ancestry.event_type import EventType
    from betty.ancestry.file_reference import FileReference
    from betty.ancestry.note import Note
    from betty.date import DateLike
    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
@EntityDefinition(
    "event",
    label=_("Event"),
    label_plural=_("Events"),
    label_countable=ngettext("{count} event", "{count} events"),
)
class Event(
    HasDate,
    HasFileReferences,
    HasCitations,
    HasNotes,
    HasDescription,
    HasPrivacy,
    HasLinks,
):
    """
    An event that took place.
    """

    name = OptionalLocalizableAttr("required")
    """
    The event's name, if it has any.
    """

    place = BidirectionalToZeroOrOne["Event", Place](
        "betty.ancestry.event:Event",
        "place",
        "betty.ancestry.place:Place",
        "events",
        title="Place",
        description="The location of the event",
    )
    """
    The place the event happened.
    """
    presences = BidirectionalToManySingleType["Event", Presence](
        "betty.ancestry.event:Event",
        "presences",
        "betty.ancestry.presence:Presence",
        "event",
        title="Presences",
        description="People's presences at this event",
        linked_data_embedded=True,
    )
    """
    People's presences at this event.
    """

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        event_type: EventType | None = None,
        date: DateLike | None = None,
        file_references: ToManyAssociates[FileReference] | None = None,
        citations: ToManyAssociates[Citation] | None = None,
        notes: ToManyAssociates[Note] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        place: ToZeroOrOneAssociate[Place] = None,
        description: LocalizableLike | None = None,
        presences: ToManyAssociates[Presence] | None = None,
        name: LocalizableLike | None = None,
    ):
        super().__init__(
            id,
            date=date,
            file_references=file_references,
            citations=citations,
            notes=notes,
            privacy=privacy,
            public=public,
            private=private,
            description=description,
        )
        self._event_type = event_type or UnknownEventType()
        if place is not None:
            self.place = place
        if presences is not None:
            self.presences = presences
        self.name = name

    @override
    def get_mutables(self) -> Iterable[object]:
        return (
            *super().get_mutables(),
            self.event_type,
        )

    @override
    def dated_linked_data_contexts(self) -> tuple[str | None, str | None, str | None]:
        return (
            "https://schema.org/startDate",
            "https://schema.org/startDate",
            "https://schema.org/endDate",
        )

    @override
    @property
    def label(self) -> Localizable:
        if self.name:
            return self.name

        format_kwargs: Mapping[str, LocalizableLike] = {
            "event_type": self._event_type.plugin().label,
        }
        subjects = [
            presence.person
            for presence in self.presences
            if presence.public
            and isinstance(presence.role, Subject)
            and presence.person.public
        ]
        if subjects:
            format_kwargs["subjects"] = AllEnumeration(
                *(person.label for person in subjects)
            )

        if subjects:
            return _("{event_type} of {subjects}").format(**format_kwargs)
        return _("{event_type}").format(**format_kwargs)

    @property
    def event_type(self) -> EventType:
        """
        The type of event.
        """
        return self._event_type

    @override
    async def dump_linked_data(self, project: Project, /) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(dump, place="https://schema.org/location")
        dump_context(dump, presences="https://schema.org/performer")
        dump["@type"] = "https://schema.org/Event"
        dump["type"] = self.event_type.plugin().id
        dump["eventAttendanceMode"] = "https://schema.org/OfflineEventAttendanceMode"
        dump["eventStatus"] = "https://schema.org/EventScheduled"
        if self.name is not None:
            dump["name"] = dump_linked_data(
                self.name, localizers=await project.public_localizers
            )
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "name",
            StaticTranslationsSchema(),
            False,
        )
        schema.add_property(
            "type",
            PluginIdSchema(
                EventTypeDefinition.type(), await project.plugins(EventTypeDefinition)
            ),
        )
        schema.add_property("eventStatus", String(title="Event status"))
        schema.add_property(
            "eventAttendanceMode", String(title="Event attendance mode")
        )
        return schema
