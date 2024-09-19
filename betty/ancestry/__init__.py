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
from betty.ancestry.gender.genders import Unknown as UnknownGender
from betty.ancestry.has_citations import HasCitations
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import Link, HasLinks
from betty.ancestry.locale import HasLocale
from betty.ancestry.media_type import HasMediaType
from betty.ancestry.note import Note, HasNotes
from betty.ancestry.place import Place
from betty.ancestry.presence_role import PresenceRole, PresenceRoleSchema
from betty.ancestry.presence_role.presence_roles import Subject
from betty.ancestry.privacy import HasPrivacy, Privacy, merge_privacies
from betty.asyncio import wait_to_thread
from betty.classtools import repr_instance
from betty.functools import Uniquifier
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
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import (
    _,
    Localizable,
    call,
    ShorthandStaticTranslations,
    StaticTranslationsLocalizableSchema,
    OptionalStaticTranslationsLocalizableAttr,
)
from betty.model import (
    Entity,
    UserFacingEntity,
    GeneratedEntityId,
    EntityReferenceCollectionSchema,
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
from betty.string import camel_case_to_kebab_case

if TYPE_CHECKING:
    from betty.date import Datey
    from betty.media_type import MediaType
    from betty.ancestry.event_type import EventType
    from betty.ancestry.gender import Gender
    from betty.serde.dump import DumpMapping, Dump
    from betty.image import FocusArea
    from betty.project import Project
    from pathlib import Path
    from collections.abc import MutableSequence, Iterator, Mapping


@final
class File(
    ShorthandPluginBase,
    HasDescription,
    HasPrivacy,
    HasLinks,
    HasMediaType,
    HasNotes,
    HasCitations,
    UserFacingEntity,
    Entity,
):
    """
    A file on disk.

    This includes but is not limited to:

    - images
    - video
    - audio
    - PDF documents
    """

    _plugin_id = "file"
    _plugin_label = _("File")

    referees = OneToMany["File", "FileReference"](
        "betty.ancestry:File",
        "referees",
        "betty.ancestry:FileReference",
        "file",
    )

    def __init__(
        self,
        path: Path,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        name: str | None = None,
        media_type: MediaType | None = None,
        description: ShorthandStaticTranslations | None = None,
        notes: Iterable[Note] | None = None,
        citations: Iterable[Citation] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        links: MutableSequence[Link] | None = None,
    ):
        super().__init__(
            id,
            media_type=media_type,
            description=description,
            notes=notes,
            citations=citations,
            privacy=privacy,
            public=public,
            private=private,
            links=links,
        )
        self._path = path
        self._name = name

    @property
    def name(self) -> str:
        """
        The file name.
        """
        return self._name or self.path.name

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Files")

    @property
    def path(self) -> Path:
        """
        The file's path on disk.
        """
        return self._path

    @override
    @property
    def label(self) -> Localizable:
        return self.description or super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["entities"] = [
            project.static_url_generator.generate(
                f"/{camel_case_to_kebab_case(file_reference.referee.plugin_id())}/{quote(file_reference.referee.id)}/index.json"
            )
            for file_reference in self.referees
            if file_reference.referee
            and not isinstance(file_reference.referee.id, GeneratedEntityId)
        ]
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "entities",
            Array(
                String(format=String.Format.URI),
                title="Entities",
                description="The entities this file is associated with",
            ),
        )
        return schema


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
class Source(
    ShorthandPluginBase,
    HasDate,
    HasFileReferences,
    HasNotes,
    HasLinks,
    HasPrivacy,
    UserFacingEntity,
    Entity,
):
    """
    A source of information.
    """

    _plugin_id = "source"
    _plugin_label = _("Source")

    #: The source this one is directly contained by.
    contained_by = ManyToOne["Source", "Source"](
        "betty.ancestry:Source",
        "contained_by",
        "betty.ancestry:Source",
        "contains",
    )
    contains = OneToMany["Source", "Source"](
        "betty.ancestry:Source",
        "contains",
        "betty.ancestry:Source",
        "contained_by",
    )
    citations = OneToMany["Source", "Citation"](
        "betty.ancestry:Source",
        "citations",
        "betty.ancestry:Citation",
        "source",
    )

    #: The human-readable source name.
    name = OptionalStaticTranslationsLocalizableAttr("name")

    #: The human-readable author.
    author = OptionalStaticTranslationsLocalizableAttr("author")

    #: The human-readable publisher.
    publisher = OptionalStaticTranslationsLocalizableAttr("publisher")

    def __init__(
        self,
        name: ShorthandStaticTranslations | None = None,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        author: ShorthandStaticTranslations | None = None,
        publisher: ShorthandStaticTranslations | None = None,
        contained_by: Source | None = None,
        contains: Iterable[Source] | None = None,
        notes: Iterable[Note] | None = None,
        date: Datey | None = None,
        file_references: Iterable[FileReference] | None = None,
        links: MutableSequence[Link] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            notes=notes,
            date=date,
            file_references=file_references,
            links=links,
            privacy=privacy,
            public=public,
            private=private,
        )
        if name:
            self.name = name
        if author:
            self.author = author
        if publisher:
            self.publisher = publisher
        if contained_by is not None:
            self.contained_by = contained_by
        if contains is not None:
            self.contains = contains

    @override
    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.contained_by:
            return merge_privacies(privacy, self.contained_by.privacy)
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
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Sources")

    @override
    @property
    def label(self) -> Localizable:
        return self.name if self.name else super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        dump["contains"] = [
            project.static_url_generator.generate(
                f"/source/{quote(contained.id)}/index.json"
            )
            for contained in self.contains
            if not isinstance(contained.id, GeneratedEntityId)
        ]
        dump["citations"] = [
            project.static_url_generator.generate(
                f"/citation/{quote(citation.id)}/index.json"
            )
            for citation in self.citations
            if not isinstance(citation.id, GeneratedEntityId)
        ]
        if self.contained_by is not None and not isinstance(
            self.contained_by.id, GeneratedEntityId
        ):
            dump["containedBy"] = project.static_url_generator.generate(
                f"/source/{quote(self.contained_by.id)}/index.json"
            )
        if self.public:
            if self.name:
                dump_context(dump, name="https://schema.org/name")
                dump["name"] = await self.name.dump_linked_data(project)
            if self.author:
                dump["author"] = await self.author.dump_linked_data(project)
            if self.publisher:
                dump["publisher"] = await self.publisher.dump_linked_data(project)
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "name", StaticTranslationsLocalizableSchema(title="Name"), False
        )
        schema.add_property(
            "author", StaticTranslationsLocalizableSchema(title="Author"), False
        )
        schema.add_property(
            "publisher", StaticTranslationsLocalizableSchema(title="Publisher"), False
        )
        schema.add_property("contains", EntityReferenceCollectionSchema(Source))
        schema.add_property("citations", EntityReferenceCollectionSchema(Citation))
        schema.add_property("containedBy", EntityReferenceSchema(Source), False)
        return schema


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
class Enclosure(ShorthandPluginBase, HasDate, HasCitations, Entity):
    """
    The enclosure of one place by another.

    Enclosures describe the outer (```enclosed_by`) and inner(``encloses``) places, and their relationship.
    """

    _plugin_id = "enclosure"
    _plugin_label = _("Enclosure")

    #: The outer place.
    enclosed_by = ManyToOne["Enclosure", "Place"](
        "betty.ancestry:Enclosure",
        "enclosed_by",
        "betty.ancestry:Place",
        "encloses",
    )
    #: The inner place.
    encloses = ManyToOne["Enclosure", "Place"](
        "betty.ancestry:Enclosure",
        "encloses",
        "betty.ancestry:Place",
        "enclosed_by",
    )

    def __init__(
        self,
        encloses: Place | None = None,
        enclosed_by: Place | None = None,
    ):
        super().__init__()
        self.encloses = encloses
        self.enclosed_by = enclosed_by

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Enclosures")


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
class PersonName(ShorthandPluginBase, HasLocale, HasCitations, HasPrivacy, Entity):
    """
    A name for a :py:class:`betty.ancestry.Person`.
    """

    _plugin_id = "person-name"
    _plugin_label = _("Person name")

    #: The person whose name this is.
    person = ManyToOne["PersonName", "Person"](
        "betty.ancestry:PersonName",
        "person",
        "betty.ancestry:Person",
        "names",
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        person: Person | None = None,
        individual: str | None = None,
        affiliation: str | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        locale: str = UNDETERMINED_LOCALE,
    ):
        if not individual and not affiliation:
            raise ValueError(
                "The individual and affiliation names must not both be empty."
            )
        super().__init__(
            id,
            privacy=privacy,
            public=public,
            private=private,
            locale=locale,
        )
        self._individual = individual
        self._affiliation = affiliation
        # Set the person association last, because the association requires comparisons, and self.__eq__() uses the
        # individual and affiliation names.
        self.person = person

    @override
    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.person:
            return merge_privacies(privacy, self.person.privacy)
        return privacy

    @override
    def __repr__(self) -> str:
        return repr_instance(
            self, id=self.id, individual=self.individual, affiliation=self.affiliation
        )

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Person names")

    @property
    def individual(self) -> str | None:
        """
        The name's individual component.

        Also known as:

        - first name
        - given name
        """
        return self._individual

    @property
    def affiliation(self) -> str | None:
        """
        The name's affiliation, or family component.

        Also known as:

        - last name
        - surname
        """
        return self._affiliation

    @override
    @property
    def label(self) -> Localizable:
        return _("{individual_name} {affiliation_name}").format(
            individual_name="…" if not self.individual else self.individual,
            affiliation_name="…" if not self.affiliation else self.affiliation,
        )

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.public:
            if self.individual is not None:
                dump_context(dump, individual="https://schema.org/givenName")
                dump["individual"] = self.individual
            if self.affiliation is not None:
                dump_context(dump, affiliation="https://schema.org/familyName")
                dump["affiliation"] = self.affiliation
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "individual",
            String(
                title="Individual name",
                description="The part of the name unique to this individual, such as a first name.",
            ),
            False,
        )
        schema.add_property(
            "affiliation",
            String(
                title="Affiliation name",
                description="The part of the name shared with others, such as a surname.",
            ),
            False,
        )
        return schema


@final
class Person(
    ShorthandPluginBase,
    HasFileReferences,
    HasCitations,
    HasNotes,
    HasLinks,
    HasPrivacy,
    UserFacingEntity,
    Entity,
):
    """
    A person.
    """

    _plugin_id = "person"
    _plugin_label = _("Person")

    parents = ManyToMany["Person", "Person"](
        "betty.ancestry:Person",
        "parents",
        "betty.ancestry:Person",
        "children",
    )
    children = ManyToMany["Person", "Person"](
        "betty.ancestry:Person",
        "children",
        "betty.ancestry:Person",
        "parents",
    )
    presences = OneToMany["Person", Presence](
        "betty.ancestry:Person",
        "presences",
        "betty.ancestry:Presence",
        "person",
    )
    names = OneToMany["Person", PersonName](
        "betty.ancestry:Person",
        "names",
        "betty.ancestry:PersonName",
        "person",
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        file_references: Iterable[FileReference] | None = None,
        citations: Iterable[Citation] | None = None,
        links: MutableSequence[Link] | None = None,
        notes: Iterable[Note] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        parents: Iterable[Person] | None = None,
        children: Iterable[Person] | None = None,
        presences: Iterable[Presence] | None = None,
        names: Iterable[PersonName] | None = None,
        gender: Gender | None = None,
    ):
        super().__init__(
            id,
            file_references=file_references,
            citations=citations,
            links=links,
            notes=notes,
            privacy=privacy,
            public=public,
            private=private,
        )
        if children is not None:
            self.children = children
        if parents is not None:
            self.parents = parents
        if presences is not None:
            self.presences = presences
        if names is not None:
            self.names = names
        self.gender = gender or UnknownGender()

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("People")

    @property
    def ancestors(self) -> Iterator[Person]:
        """
        All ancestors.
        """
        for parent in self.parents:
            yield parent
            yield from parent.ancestors

    @property
    def siblings(self) -> Iterator[Person]:
        """
        All siblings.
        """
        yield from Uniquifier(
            sibling
            for parent in self.parents
            for sibling in parent.children
            if sibling != self
        )

    @property
    def descendants(self) -> Iterator[Person]:
        """
        All descendants.
        """
        for child in self.children:
            yield child
            yield from child.descendants

    @override
    @property
    def label(self) -> Localizable:
        for name in self.names:
            if name.public:
                return name.label
        return super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(
            dump,
            names="https://schema.org/name",
            parents="https://schema.org/parent",
            children="https://schema.org/child",
            siblings="https://schema.org/sibling",
        )
        dump["@type"] = "https://schema.org/Person"
        dump["parents"] = [
            project.static_url_generator.generate(
                f"/person/{quote(parent.id)}/index.json"
            )
            for parent in self.parents
            if not isinstance(parent.id, GeneratedEntityId)
        ]
        dump["children"] = [
            project.static_url_generator.generate(
                f"/person/{quote(child.id)}/index.json"
            )
            for child in self.children
            if not isinstance(child.id, GeneratedEntityId)
        ]
        dump["siblings"] = [
            project.static_url_generator.generate(
                f"/person/{quote(sibling.id)}/index.json"
            )
            for sibling in self.siblings
            if not isinstance(sibling.id, GeneratedEntityId)
        ]
        dump["presences"] = [
            self._dump_person_presence(presence, project)
            for presence in self.presences
            if presence.event is not None
            and not isinstance(presence.event.id, GeneratedEntityId)
        ]
        if self.public:
            dump["names"] = [
                await name.dump_linked_data(project)
                for name in self.names
                if name.public
            ]
            dump["gender"] = self.gender.plugin_id()
        else:
            dump["names"] = []
        return dump

    def _dump_person_presence(
        self, presence: Presence, project: Project
    ) -> DumpMapping[Dump]:
        assert presence.event
        dump: DumpMapping[Dump] = {
            "event": project.static_url_generator.generate(
                f"/event/{quote(presence.event.id)}/index.json"
            ),
        }
        dump_context(dump, event="https://schema.org/performerIn")
        if presence.public:
            dump["role"] = presence.role.plugin_id()
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "names",
            Array(await PersonName.linked_data_schema(project), title="Names"),
        )
        schema.add_property(
            "gender",
            Enum(
                *[gender.plugin_id() async for gender in project.genders],
                title="Gender",
            ),
            property_required=False,
        )
        schema.add_property("parents", EntityReferenceCollectionSchema(Person))
        schema.add_property("children", EntityReferenceCollectionSchema(Person))
        schema.add_property("siblings", EntityReferenceCollectionSchema(Person))
        schema.add_property(
            "presences", Array(_PersonPresenceSchema(), title="Presences")
        )
        return schema


class _PersonPresenceSchema(JsonLdObject):
    """
    A schema for the :py:class:`betty.ancestry.Presence` associations on a :py:class:`betty.ancestry.Person`.
    """

    def __init__(self):
        super().__init__(title="Presence (person)")
        self.add_property("role", PresenceRoleSchema(), False)
        self.add_property("event", EntityReferenceSchema(Event))


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
