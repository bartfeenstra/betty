"""
Provide Betty's main data model.
"""

from __future__ import annotations

from reprlib import recursive_repr
from typing import Iterable, TYPE_CHECKING, final
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.description import HasDescription
from betty.ancestry.event_type import EVENT_TYPE_REPOSITORY
from betty.ancestry.event_type.event_types import Unknown as UnknownEventType
from betty.ancestry.file import File
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import HasLinks
from betty.ancestry.note import Note, HasNotes
from betty.ancestry.person import Person
from betty.ancestry.place import Place
from betty.ancestry.presence_role import PresenceRole, PresenceRoleSchema
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.privacy import HasPrivacy, Privacy, merge_privacies
from betty.ancestry.source import Source
from betty.asyncio import wait_to_thread
from betty.classtools import repr_instance
from betty.json.linked_data import (
    dump_context,
    JsonLdObject,
)
from betty.json.schema import (
    Array,
    String,
    Object,
    Enum,
)
from betty.locale.localizable import (
    _,
    Localizable,
    call,
    ShorthandStaticTranslations,
    OptionalStaticTranslationsLocalizableAttr,
)
from betty.model import (
    Entity,
    UserFacingEntity,
    GeneratedEntityId,
    EntityReferenceSchema,
)
from betty.model.association import (
    ManyToOne,
    OneToMany,
    ManyToMany,
    AssociationRegistry,
)
from betty.model.collections import (
    MultipleTypesEntityCollection,
)
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.date import Datey
    from betty.ancestry.event_type import EventType
    from betty.serde.dump import DumpMapping, Dump
    from betty.image import FocusArea
    from betty.project import Project
    from collections.abc import Mapping


class FileReference(ShorthandPluginBase, Entity):
    """
    A reference between :py:class:`betty.ancestry.HasFileReferences` and betty.ancestry.File.

    This reference holds additional information specific to the relationship between the two entities.
    """

    _plugin_id = "file-reference"
    _plugin_label = _("File reference")

    #: The entity that references the file.
    referee = ManyToOne["FileReference", "HasFileReferences"](
        "betty.ancestry:FileReference",
        "referee",
        "betty.ancestry:HasFileReferences",
        "file_references",
    )
    #: The referenced file.
    file = ManyToOne["FileReference", File](
        "betty.ancestry:FileReference",
        "file",
        "betty.ancestry:File",
        "referees",
    )

    def __init__(
        self,
        referee: HasFileReferences & Entity | None = None,
        file: File | None = None,
        focus: FocusArea | None = None,
    ):
        super().__init__()
        self.referee = referee
        self.file = file
        self.focus = focus

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("File references")

    @property
    def focus(self) -> FocusArea | None:
        """
        The area within the 2-dimensional representation of the file to focus on.

        This can be used to locate where faces are in a photo, or a specific article in a newspaper scan, for example.
        """
        return self._focus

    @focus.setter
    def focus(self, focus: FocusArea | None) -> None:
        self._focus = focus


@final
class Citation(
    ShorthandPluginBase,
    HasDate,
    HasFileReferences,
    HasPrivacy,
    HasLinks,
    UserFacingEntity,
):
    """
    A citation (a reference to a source).
    """

    _plugin_id = "citation"
    _plugin_label = _("Citation")

    facts = ManyToMany["Citation", HasCitations](
        "betty.ancestry:Citation",
        "facts",
        "betty.ancestry.has_citations:HasCitations",
        "citations",
    )
    source = ManyToOne["Citation", Source](
        "betty.ancestry:Citation",
        "source",
        "betty.ancestry:Source",
        "citations",
    )

    #: The human-readable citation location.
    location = OptionalStaticTranslationsLocalizableAttr("location")

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        facts: Iterable[HasCitations & Entity] | None = None,
        source: Source | None = None,
        location: ShorthandStaticTranslations | None = None,
        date: Datey | None = None,
        file_references: Iterable[FileReference] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            date=date,
            file_references=file_references,
            privacy=privacy,
            public=public,
            private=private,
        )
        if facts is not None:
            self.facts = facts
        if location:
            self.location = location
        self.source = source

    @override
    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.source:
            return merge_privacies(privacy, self.source.privacy)
        return privacy

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Citations")

    @override
    @property
    def label(self) -> Localizable:
        return self.location or super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        dump["facts"] = [
            project.static_url_generator.generate(
                f"/{fact.plugin_id()}/{quote(fact.id)}/index.json"
            )
            for fact in self.facts
            if not isinstance(fact.id, GeneratedEntityId)
        ]
        if self.source is not None and not isinstance(
            self.source.id, GeneratedEntityId
        ):
            dump["source"] = project.static_url_generator.generate(
                f"/source/{quote(self.source.id)}/index.json"
            )
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "source", EntityReferenceSchema(Source, title="Source"), False
        )
        schema.add_property(
            "facts",
            Array(
                String(
                    format=String.Format.URI,
                    title="Fact",
                    description="A reference to a JSON resource that is a fact referencing this citation.",
                ),
                title="Facts",
            ),
        )
        return schema


@final
class Presence(ShorthandPluginBase, HasPrivacy, Entity):
    """
    The presence of a :py:class:`betty.ancestry.Person` at an :py:class:`betty.ancestry.Event`.
    """

    _plugin_id = "presence"
    _plugin_label = _("Presence")

    #: The person whose presence is described.
    person = ManyToOne["Presence", "Person"](
        "betty.ancestry:Presence",
        "person",
        "betty.ancestry:Person",
        "presences",
    )
    #: The event the person was present at.
    event = ManyToOne["Presence", "Event"](
        "betty.ancestry:Presence",
        "event",
        "betty.ancestry:Event",
        "presences",
    )
    #: The role the person performed at the event.
    role: PresenceRole

    def __init__(
        self,
        person: Person | None,
        role: PresenceRole,
        event: Event | None,
    ):
        super().__init__(None)
        self.person = person
        self.role = role
        self.event = event

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Presences")

    @override
    @property
    def label(self) -> Localizable:
        return _("Presence of {person} at {event}").format(
            person=self.person.label if self.person else _("Unknown"),
            event=self.event.label if self.event else _("Unknown"),
        )

    @override
    def _get_effective_privacy(self) -> Privacy:
        return merge_privacies(
            super()._get_effective_privacy(),
            self.person,
            self.event,
        )


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
    place = ManyToOne["Event", Place](
        "betty.ancestry:Event", "place", "betty.ancestry:Place", "events"
    )
    presences = OneToMany["Event", Presence](
        "betty.ancestry:Event",
        "presences",
        "betty.ancestry:Presence",
        "event",
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        event_type: EventType | None = None,
        date: Datey | None = None,
        file_references: Iterable[FileReference] | None = None,
        citations: Iterable[Citation] | None = None,
        notes: Iterable[Note] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        place: Place | None = None,
        description: ShorthandStaticTranslations | None = None,
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
            and presence.person is not None
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
        dump_context(dump, presences="https://schema.org/performer")
        dump["@type"] = "https://schema.org/Event"
        dump["type"] = self.event_type.plugin_id()
        dump["eventAttendanceMode"] = "https://schema.org/OfflineEventAttendanceMode"
        dump["eventStatus"] = "https://schema.org/EventScheduled"
        dump["presences"] = presences = []
        for presence in self.presences:
            if presence.person and not isinstance(
                presence.person.id, GeneratedEntityId
            ):
                presences.append(self._dump_event_presence(presence, project))
        if self.place is not None and not isinstance(self.place.id, GeneratedEntityId):
            dump["place"] = project.static_url_generator.generate(
                f"/place/{quote(self.place.id)}/index.json"
            )
            dump_context(dump, place="https://schema.org/location")
        return dump

    def _dump_event_presence(
        self, presence: Presence, project: Project
    ) -> DumpMapping[Dump]:
        assert presence.person
        dump: DumpMapping[Dump] = {
            "@type": "https://schema.org/Person",
            "person": project.static_url_generator.generate(
                f"/person/{quote(presence.person.id)}/index.json"
            ),
        }
        if presence.public:
            dump["role"] = presence.role.plugin_id()
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "type",
            Enum(
                *[
                    presence_role.plugin_id()
                    for presence_role in wait_to_thread(EVENT_TYPE_REPOSITORY.select())
                ],
                title="Event type",
            ),
        )
        schema.add_property("place", EntityReferenceSchema(Place), False)
        schema.add_property(
            "presences", Array(_EventPresenceSchema(), title="Presences")
        )
        schema.add_property("eventStatus", String(title="Event status"))
        schema.add_property(
            "eventAttendanceMode", String(title="Event attendance mode")
        )
        return schema


class _EventPresenceSchema(JsonLdObject):
    """
    A schema for the :py:class:`betty.ancestry.Presence` associations on a :py:class:`betty.ancestry.Event`.
    """

    def __init__(self):
        super().__init__(title="Presence (event)")
        self.add_property("role", PresenceRoleSchema(), False)
        self.add_property("person", EntityReferenceSchema(Person))


@final
class Ancestry(MultipleTypesEntityCollection[Entity]):
    """
    An ancestry contains all the entities of a single family tree/genealogical data set.
    """

    def __init__(self):
        super().__init__()
        self._check_graph = True

    def add_unchecked_graph(self, *entities: Entity) -> None:
        """
        Add entities to the ancestry but do not automatically add associates as well.

        It is the caller's responsibility to ensure all associates are added to the ancestry.
        If this is done, calling this method is faster than the usual entity collection methods.
        """
        self._check_graph = False
        try:
            self.add(*entities)
        finally:
            self._check_graph = True

    def _on_add(self, *entities: Entity) -> None:
        super()._on_add(*entities)
        if self._check_graph:
            self.add(*self._get_associates(*entities))

    def _get_associates(self, *entities: Entity) -> Iterable[Entity]:
        for entity in entities:
            for association in AssociationRegistry.get_all_associations(entity):
                for associate in AssociationRegistry.get_associates(
                    entity, association
                ):
                    yield associate
