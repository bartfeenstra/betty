"""
Provide Betty's main data model.
"""

from __future__ import annotations

import enum
from contextlib import suppress
from reprlib import recursive_repr
from typing import Iterable, Any, TYPE_CHECKING, final
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.event_type import (
    EventType,
    Unknown as UnknownEventType,
    EVENT_TYPE_REPOSITORY,
)
from betty.ancestry.gender.genders import Unknown as UnknownGender
from betty.ancestry.place_type.place_types import Unknown as UnknownPlaceType
from betty.ancestry.presence_role import PresenceRole, PresenceRoleSchema
from betty.ancestry.presence_role.presence_roles import Subject
from betty.asyncio import wait_to_thread
from betty.classtools import repr_instance
from betty.functools import Uniquifier
from betty.json.linked_data import (
    LinkedDataDumpable,
    dump_context,
    dump_link,
    JsonLdObject,
)
from betty.json.schema import (
    Array,
    String,
    Object,
    Boolean,
    Enum,
    Number,
)
from betty.locale import UNDETERMINED_LOCALE, LocaleSchema
from betty.locale.date import Datey, DateySchema, Date
from betty.locale.localizable import (
    _,
    Localizable,
    call,
    ShorthandStaticTranslations,
    StaticTranslationsLocalizableSchema,
    StaticTranslationsLocalizable,
    OptionalStaticTranslationsLocalizableAttr,
    RequiredStaticTranslationsLocalizableAttr,
)
from betty.locale.localized import Localized
from betty.media_type import MediaType, MediaTypeSchema, HTML, JSON_LD
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
    from betty.ancestry.gender import Gender
    from betty.ancestry.place_type import PlaceType
    from betty.serde.dump import DumpMapping, Dump
    from betty.image import FocusArea
    from betty.project import Project
    from geopy import Point
    from pathlib import Path
    from collections.abc import MutableSequence, Iterator, Mapping


class Privacy(enum.Enum):
    """
    The available privacy modes.
    """

    #: The resource is explicitly made public.
    PUBLIC = 1

    #: The resource is explicitly made private.
    PRIVATE = 2

    #: The resource has no explicit privacy. This means that:
    #:
    #: - it may be changed at will
    #: - when checking access, UNDETERMINED evaluates to PUBLIC.
    UNDETERMINED = 3


class HasPrivacy(LinkedDataDumpable[Object]):
    """
    A resource that has privacy.
    """

    def __init__(
        self,
        *args: Any,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if [privacy, public, private].count(None) < 2:
            raise ValueError(
                f"Only one of the `privacy`, `public`, and `private` arguments to {type(self)}.__init__() may be given at a time."
            )
        if privacy is not None:
            self._privacy = privacy
        elif public is True:
            self._privacy = Privacy.PUBLIC
        elif private is True:
            self._privacy = Privacy.PRIVATE
        else:
            self._privacy = Privacy.UNDETERMINED

    @property
    def own_privacy(self) -> Privacy:
        """
        The resource's own privacy.

        This returns the value that was set for :py:attr:`betty.ancestry.HasPrivacy.privacy` and ignores computed privacies.

        For access control and permissions checking, use :py:attr:`betty.ancestry.HasPrivacy.privacy`.
        """
        return self._privacy

    def _get_effective_privacy(self) -> Privacy:
        return self.own_privacy

    @property
    def privacy(self) -> Privacy:
        """
        The resource's privacy.
        """
        return self._get_effective_privacy()

    @privacy.setter
    def privacy(self, privacy: Privacy) -> None:
        self._privacy = privacy

    @privacy.deleter
    def privacy(self) -> None:
        self.privacy = Privacy.UNDETERMINED

    @property
    def private(self) -> bool:
        """
        Whether this resource is private.
        """
        return self.privacy is Privacy.PRIVATE

    @private.setter
    def private(self, private: True) -> None:
        self.privacy = Privacy.PRIVATE

    @property
    def public(self) -> bool:
        """
        Whether this resource is public.
        """
        # Undetermined privacy defaults to public.
        return self.privacy is not Privacy.PRIVATE

    @public.setter
    def public(self, public: True) -> None:
        self.privacy = Privacy.PUBLIC

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["private"] = self.private
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("private", PrivacySchema())
        return schema


class PrivacySchema(Boolean):
    """
    A JSON Schema for privacy.
    """

    def __init__(self):
        super().__init__(
            def_name="privacy",
            title="Privacy",
            description="Whether this entity is private (true), or public (false).",
        )


def is_private(target: Any) -> bool:
    """
    Check if the given target is private.
    """
    if isinstance(target, HasPrivacy):
        return target.private
    return False


def is_public(target: Any) -> bool:
    """
    Check if the given target is public.
    """
    if isinstance(target, HasPrivacy):
        return target.public
    return True


def resolve_privacy(privacy: Privacy | HasPrivacy | None) -> Privacy:
    """
    Resolve the privacy of a value.
    """
    if privacy is None:
        return Privacy.UNDETERMINED
    if isinstance(privacy, Privacy):
        return privacy
    return privacy.privacy


def merge_privacies(*privacies: Privacy | HasPrivacy | None) -> Privacy:
    """
    Merge multiple privacies into one.
    """
    privacies = {resolve_privacy(privacy) for privacy in privacies}
    if Privacy.PRIVATE in privacies:
        return Privacy.PRIVATE
    if Privacy.UNDETERMINED in privacies:
        return Privacy.UNDETERMINED
    return Privacy.PUBLIC


class HasDate(LinkedDataDumpable[Object]):
    """
    A resource with date information.
    """

    def __init__(
        self,
        *args: Any,
        date: Datey | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.date = date

    def dated_linked_data_contexts(self) -> tuple[str | None, str | None, str | None]:
        """
        Get the JSON-LD context term definition IRIs for the possible dates.

        :returns: A 3-tuple with the IRI for a single date, a start date, and an end date, respectively.
        """
        return None, None, None

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.date and is_public(self):
            (
                schema_org_date_definition,
                schema_org_start_date_definition,
                schema_org_end_date_definition,
            ) = self.dated_linked_data_contexts()
            if isinstance(self.date, Date):
                dump["date"] = await self.date.dump_linked_data(
                    project, schema_org_date_definition
                )
            else:
                dump["date"] = await self.date.dump_linked_data(
                    project,
                    schema_org_start_date_definition,
                    schema_org_end_date_definition,
                )
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("date", DateySchema(), False)
        return schema


class HasDescription(LinkedDataDumpable[Object]):
    """
    A resource with a description.
    """

    #: The human-readable description.
    description = OptionalStaticTranslationsLocalizableAttr("description")

    def __init__(
        self,
        *args: Any,
        description: ShorthandStaticTranslations | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if description is not None:
            self.description.replace(description)

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.description:
            dump["description"] = await self.description.dump_linked_data(project)
            dump_context(dump, description="https://schema.org/description")
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("description", StaticTranslationsLocalizableSchema(), False)
        return schema


class HasMediaType(LinkedDataDumpable[Object]):
    """
    A resource with an `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
    """

    def __init__(
        self,
        *args: Any,
        media_type: MediaType | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.media_type = media_type

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if is_public(self) and self.media_type is not None:
            dump["mediaType"] = str(self.media_type)
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("mediaType", MediaTypeSchema(), False)
        return schema


class HasLocale(Localized, LinkedDataDumpable[Object]):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    def __init__(
        self,
        *args: Any,
        locale: str = UNDETERMINED_LOCALE,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._locale = locale

    @override
    @property
    def locale(self) -> str:
        return self._locale

    @locale.setter
    def locale(self, locale: str) -> None:
        self._locale = locale

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["locale"] = self.locale
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("locale", LocaleSchema())
        return schema


class LinkSchema(JsonLdObject):
    """
    A JSON Schema for :py:class:`betty.ancestry.Link`.
    """

    def __init__(self):
        super().__init__(def_name="link", title="Link")
        self.add_property(
            "url",
            String(
                format=String.Format.URI,
                description="The full URL to the other resource.",
            ),
        )
        self.add_property(
            "relationship",
            String(
                description="The relationship between this resource and the link target (https://en.wikipedia.org/wiki/Link_relation)."
            ),
            False,
        )
        self.add_property(
            "label",
            StaticTranslationsLocalizableSchema(
                title="Label", description="The human-readable link label."
            ),
            False,
        )


class LinkCollectionSchema(Array):
    """
    A JSON Schema for :py:class:`betty.ancestry.Link` collections.
    """

    def __init__(self):
        super().__init__(LinkSchema(), def_name="linkCollection", title="Links")


@final
class Link(HasMediaType, HasLocale, HasDescription, LinkedDataDumpable[Object]):
    """
    An external link.
    """

    #: The link's absolute URL
    url: str
    #: The link's `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.
    relationship: str | None
    #: The link's human-readable label.
    label = OptionalStaticTranslationsLocalizableAttr("label")

    def __init__(
        self,
        url: str,
        *,
        relationship: str | None = None,
        label: ShorthandStaticTranslations | None = None,
        description: ShorthandStaticTranslations | None = None,
        media_type: MediaType | None = None,
        locale: str = UNDETERMINED_LOCALE,
    ):
        super().__init__(
            media_type=media_type,
            description=description,
            locale=locale,
        )
        self.url = url
        if label:
            self.label = label
        self.relationship = relationship

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["url"] = self.url
        if self.label:
            dump["label"] = await self.label.dump_linked_data(project)
        if self.relationship is not None:
            dump["relationship"] = self.relationship
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> LinkSchema:
        return LinkSchema()


class HasLinks(Entity):
    """
    A resource that has external links.
    """

    def __init__(
        self,
        *args: Any,
        links: MutableSequence[Link] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._links: MutableSequence[Link] = links if links else []

    @property
    def links(self) -> MutableSequence[Link]:
        """
        The extenal links.
        """
        return self._links

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        await dump_link(
            dump,
            project,
            *(self.links if is_public(self) else ()),
        )

        if not isinstance(self.id, GeneratedEntityId):
            await dump_link(
                dump,
                project,
                Link(
                    project.static_url_generator.generate(
                        f"/{self.type.plugin_id()}/{self.id}/index.json"
                    ),
                    relationship="canonical",
                    media_type=JSON_LD,
                ),
            )
            if is_public(self):
                await dump_link(
                    dump,
                    project,
                    *(
                        Link(
                            project.url_generator.generate(
                                self,
                                media_type="text/html",
                                locale=locale,
                            ),
                            relationship="alternate",
                            media_type=HTML,
                            locale=locale,
                        )
                        for locale in project.configuration.locales
                    ),
                )

        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("links", LinkCollectionSchema())
        return schema


@final
class Note(ShorthandPluginBase, UserFacingEntity, HasPrivacy, HasLinks, Entity):
    """
    A note is a bit of textual information that can be associated with another entity.
    """

    _plugin_id = "note"
    _plugin_label = _("Note")

    #: The entity the note belongs to.
    entity = ManyToOne["Note", "HasNotes"](
        "betty.ancestry:Note", "entity", "betty.ancestry:HasNotes", "notes"
    )

    #: The human-readable note text.
    text = RequiredStaticTranslationsLocalizableAttr("text")

    def __init__(
        self,
        text: ShorthandStaticTranslations,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        entity: HasNotes & Entity | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            privacy=privacy,
            public=public,
            private=private,
        )
        self.text = text
        if entity is not None:
            self.entity = entity

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Notes")

    @override
    @property
    def label(self) -> Localizable:
        return self.text

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        if self.public:
            dump["text"] = await self.text.dump_linked_data(project)
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("text", StaticTranslationsLocalizableSchema(), False)
        return schema


class HasNotes(Entity):
    """
    An entity that has notes associated with it.
    """

    notes = OneToMany["HasNotes", Note](
        "betty.ancestry:HasNotes", "notes", "betty.ancestry:Note", "entity"
    )

    def __init__(
        self: HasNotes & Entity,
        *args: Any,
        notes: Iterable[Note] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if notes is not None:
            self.notes = notes

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["notes"] = [
            project.static_url_generator.generate(f"/note/{quote(note.id)}/index.json")
            for note in self.notes
            if not isinstance(note.id, GeneratedEntityId)
        ]
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("notes", EntityReferenceCollectionSchema(Note))
        return schema


class HasCitations(Entity):
    """
    An entity with citations that support it.
    """

    citations = ManyToMany["HasCitations & Entity", "Citation"](
        "betty.ancestry:HasCitations",
        "citations",
        "betty.ancestry:Citation",
        "facts",
    )

    def __init__(
        self: HasCitations & Entity,
        *args: Any,
        citations: Iterable[Citation] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if citations is not None:
            self.citations = citations

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["citations"] = [
            project.static_url_generator.generate(
                f"/citation/{quote(citation.id)}/index.json"
            )
            for citation in self.citations
            if not isinstance(citation.id, GeneratedEntityId)
        ]
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("citations", EntityReferenceCollectionSchema(Citation))
        return schema


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


class HasFileReferences(Entity):
    """
    An entity that has associated :py:class:`betty.ancestry.File` entities.
    """

    file_references = OneToMany["HasFileReferences & Entity", FileReference](
        "betty.ancestry:HasFileReferences",
        "file_references",
        "betty.ancestry:FileReference",
        "referee",
    )

    def __init__(
        self: HasFileReferences & Entity,
        *args: Any,
        file_references: Iterable[FileReference] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if file_references is not None:
            self.file_references = file_references


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
        "betty.ancestry:HasCitations",
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
class Name(StaticTranslationsLocalizable, HasDate):
    """
    A name.

    A name can be translated, and have a date expressing the period the name was in use.
    """

    def __init__(
        self,
        translations: ShorthandStaticTranslations,
        *,
        date: Datey | None = None,
    ):
        super().__init__(
            translations,
            date=date,
        )


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
class Place(
    ShorthandPluginBase,
    HasLinks,
    HasFileReferences,
    HasNotes,
    HasPrivacy,
    UserFacingEntity,
    Entity,
):
    """
    A place.

    A place is a physical location on earth. It may be identifiable by GPS coordinates only, or
    be a well-known city, with names in many languages, imagery, and its own Wikipedia page, or
    any type of place in between.
    """

    _plugin_id = "place"
    _plugin_label = _("Place")

    events = OneToMany["Place", "Event"](
        "betty.ancestry:Place", "events", "betty.ancestry:Event", "place"
    )
    enclosed_by = OneToMany["Place", Enclosure](
        "betty.ancestry:Place",
        "enclosed_by",
        "betty.ancestry:Enclosure",
        "encloses",
    )
    encloses = OneToMany["Place", Enclosure](
        "betty.ancestry:Place",
        "encloses",
        "betty.ancestry:Enclosure",
        "enclosed_by",
    )

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002
        names: MutableSequence[Name] | None = None,
        events: Iterable[Event] | None = None,
        enclosed_by: Iterable[Enclosure] | None = None,
        encloses: Iterable[Enclosure] | None = None,
        notes: Iterable[Note] | None = None,
        coordinates: Point | None = None,
        links: MutableSequence[Link] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        place_type: PlaceType | None = None,
    ):
        super().__init__(
            id,
            notes=notes,
            links=links,
            privacy=privacy,
            public=public,
            private=private,
        )
        self._names = [] if names is None else names
        self._coordinates = coordinates
        if events is not None:
            self.events = events
        if enclosed_by is not None:
            self.enclosed_by = enclosed_by
        if encloses is not None:
            self.encloses = encloses
        self._place_type = place_type or UnknownPlaceType()

    @property
    def walk_encloses(self) -> Iterator[Enclosure]:
        """
        All enclosed places.
        """
        for enclosure in self.encloses:
            yield enclosure
            if enclosure.encloses is not None:
                yield from enclosure.encloses.walk_encloses

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Places")

    @property
    def place_type(self) -> PlaceType:
        """
        The type of this place.
        """
        return self._place_type

    @place_type.setter
    def place_type(self, place_type: PlaceType) -> None:
        self._place_type = place_type

    @property
    def names(self) -> MutableSequence[Name]:
        """
        The place's names.

        The first name is considered the :py:attr:`place label <betty.ancestry.Place.label>`.
        """
        return self._names

    @property
    def coordinates(self) -> Point | None:
        """
        The place's coordinates.
        """
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates

    @override
    @property
    def label(self) -> Localizable:
        with suppress(IndexError):
            return self.names[0]
        return super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(
            dump,
            names="https://schema.org/name",
            events="https://schema.org/event",
            enclosedBy="https://schema.org/containedInPlace",
            encloses="https://schema.org/containsPlace",
        )
        dump["@type"] = "https://schema.org/Place"
        dump["names"] = [await name.dump_linked_data(project) for name in self.names]
        dump["events"] = [
            project.static_url_generator.generate(
                f"/event/{quote(event.id)}/index.json"
            )
            for event in self.events
            if not isinstance(event.id, GeneratedEntityId)
        ]
        dump["enclosedBy"] = [
            project.static_url_generator.generate(
                f"/place/{quote(enclosure.enclosed_by.id)}/index.json"
            )
            for enclosure in self.enclosed_by
            if enclosure.enclosed_by is not None
            and not isinstance(enclosure.enclosed_by.id, GeneratedEntityId)
        ]
        dump["encloses"] = [
            project.static_url_generator.generate(
                f"/place/{quote(enclosure.encloses.id)}/index.json"
            )
            for enclosure in self.encloses
            if enclosure.encloses is not None
            and not isinstance(enclosure.encloses.id, GeneratedEntityId)
        ]
        if self.coordinates is not None:
            dump["coordinates"] = {
                "@type": "https://schema.org/GeoCoordinates",
                "latitude": self.coordinates.latitude,
                "longitude": self.coordinates.longitude,
            }
            dump_context(dump, coordinates="https://schema.org/geo")
            dump_context(
                dump["coordinates"],  # type: ignore[arg-type]
                latitude="https://schema.org/latitude",
            )
            dump_context(
                dump["coordinates"],  # type: ignore[arg-type]
                longitude="https://schema.org/longitude",
            )
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "names", Array(await Name.linked_data_schema(project), title="Names")
        )
        schema.add_property("enclosedBy", EntityReferenceCollectionSchema(Place))
        schema.add_property("encloses", EntityReferenceCollectionSchema(Place))
        coordinate_schema = Number(title="Coordinate")
        coordinates_schema = JsonLdObject(title="Coordinates")
        coordinates_schema.add_property("latitude", coordinate_schema, False)
        coordinates_schema.add_property("longitude", coordinate_schema, False)
        schema.add_property("coordinates", coordinates_schema, False)
        schema.add_property("events", EntityReferenceCollectionSchema(Event))
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
