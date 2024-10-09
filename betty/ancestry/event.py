"""
Data types to describe events.
"""

from __future__ import annotations

from reprlib import recursive_repr
from typing import final, Iterable, Mapping, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.description import HasDescription
from betty.ancestry.event_type import EVENT_TYPE_REPOSITORY, EventType
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_notes import HasNotes
from betty.ancestry.link import HasLinks
from betty.ancestry.place import Place
from betty.ancestry.presence import Presence
from betty.ancestry.presence_role.presence_roles import Subject
from betty.json.linked_data import dump_context, JsonLdObject
from betty.json.schema import Enum, String
from betty.locale.localizable import _, ShorthandStaticTranslations, Localizable, call
from betty.model import UserFacingEntity
from betty.model.association import (
    BidirectionalToZeroOrOne,
    BidirectionalToMany,
    ToManyResolver,
)
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy
from betty.repr import repr_instance

if TYPE_CHECKING:
    from betty.ancestry.citation import Citation
    from betty.ancestry.note import Note
    from betty.ancestry.file_reference import FileReference
    from betty.date import Datey
    from betty.project import Project
    from betty.serde.dump import DumpMapping, Dump


@final
class Event(
    ShorthandPluginBase,
    HasDate,
    HasFileReferences,
    HasCitations,
    HasNotes,
    HasDescription,
    HasPrivacy,
    HasLinks,
    UserFacingEntity,
):
    """
    An event that took place.
    """

    _plugin_id = "event"
    _plugin_label = _("Event")

    #: The place the event happened.
    place = BidirectionalToZeroOrOne["Event", Place](
        "betty.ancestry.event:Event",
        "place",
        "betty.ancestry.place:Place",
        "events",
        title="Place",
        description="The location of the event",
    )
    presences = BidirectionalToMany["Event", Presence](
        "betty.ancestry.event:Event",
        "presences",
        "betty.ancestry.presence:Presence",
        "event",
        title="Presences",
        description="People's presences at this event",
        linked_data_embedded=True,
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        event_type: EventType | None = None,
        date: Datey | None = None,
        file_references: Iterable[FileReference]
        | ToManyResolver[FileReference]
        | None = None,
        citations: Iterable[Citation] | ToManyResolver[Citation] | None = None,
        notes: Iterable[Note] | ToManyResolver[Note] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        place: Place | None = None,
        description: ShorthandStaticTranslations | None = None,
        presences: Iterable[Presence] | ToManyResolver[Presence] | None = None,
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
        format_kwargs: Mapping[str, str | Localizable] = {
            "event_type": self._event_type.plugin_label(),
        }
        subjects = [
            presence.person
            for presence in self.presences
            if presence.public
            and isinstance(presence.role, Subject)
            and presence.person.public
        ]
        if subjects:
            format_kwargs["subjects"] = call(
                lambda localizer: ", ".join(
                    person.label.localize(localizer) for person in subjects
                )
            )
        if self.description:
            format_kwargs["event_description"] = self.description

        if subjects:
            if self.description:
                return _("{event_type} ({event_description}) of {subjects}").format(
                    **format_kwargs
                )
            else:
                return _("{event_type} of {subjects}").format(**format_kwargs)
        if self.description:
            return _("{event_type} ({event_description})").format(**format_kwargs)
        else:
            return _("{event_type}").format(**format_kwargs)

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, id=self._id, type=self._event_type)

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Events")

    @property
    def event_type(self) -> EventType:
        """
        The type of event.
        """
        return self._event_type

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(dump, place="https://schema.org/location")
        dump_context(dump, presences="https://schema.org/performer")
        dump["@type"] = "https://schema.org/Event"
        dump["type"] = self.event_type.plugin_id()
        dump["eventAttendanceMode"] = "https://schema.org/OfflineEventAttendanceMode"
        dump["eventStatus"] = "https://schema.org/EventScheduled"
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "type",
            Enum(
                *[
                    presence_role.plugin_id()
                    async for presence_role in EVENT_TYPE_REPOSITORY
                ],
                title="Event type",
            ),
        )
        schema.add_property("eventStatus", String(title="Event status"))
        schema.add_property(
            "eventAttendanceMode", String(title="Event attendance mode")
        )
        return schema
