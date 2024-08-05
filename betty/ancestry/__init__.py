"""
Provide Betty's main data model.
"""

from __future__ import annotations

from contextlib import suppress
from enum import Enum
from reprlib import recursive_repr
from typing import Iterable, Any, TYPE_CHECKING, final, cast
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.event_type import EventType, UnknownEventType
from betty.ancestry.presence_role import PresenceRole, Subject, PresenceRoleSchema
from betty.classtools import repr_instance
from betty.functools import Uniquifier
from betty.json.linked_data import (
    LinkedDataDumpable,
    dump_context,
    dump_link,
    add_json_ld,
)
from betty.json.schema import (
    add_property,
    Schema,
    ArraySchema,
    Ref,
    LocaleSchema,
)
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.date import Datey, DateySchema
from betty.locale.localizable import (
    _,
    Localizable,
    static,
    call,
    plain,
    ShorthandStaticTranslations,
    StaticTranslationsLocalizableAttr,
    StaticTranslationsLocalizableSchema,
)
from betty.locale.localized import Localized
from betty.media_type import MediaType, MediaTypeSchema
from betty.model import (
    Entity,
    UserFacingEntity,
    GeneratedEntityId,
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
from betty.serde.dump import DumpMapping, Dump
from betty.string import camel_case_to_kebab_case

if TYPE_CHECKING:
    from betty.machine_name import MachineName
    from betty.image import FocusArea
    from betty.project import Project
    from geopy import Point
    from pathlib import Path
    from collections.abc import MutableSequence, Iterator, Mapping


class Privacy(Enum):
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


class HasPrivacy(LinkedDataDumpable):
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
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "private",
            PrivacySchema(),
        )
        return schema


class PrivacySchema(Schema):
    """
    A JSON Schema for privacy.
    """

    def __init__(self):
        super().__init__(
            name="privacy",
            schema={
                "type": "boolean",
                "description": "Whether this entity is private (true), or public (false).",
            },
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


class Dated(LinkedDataDumpable):
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

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.date and is_public(self):
            dump["date"] = await self.date.dump_linked_data(project)
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        schema.schema["type"] = "object"
        schema.schema["additionalProperties"] = False
        add_property(schema, "date", DateySchema(), False)
        return schema


class Described(LinkedDataDumpable):
    """
    A resource with a description.
    """

    #: The human-readable description.
    description = StaticTranslationsLocalizableAttr("description")

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
            dump_context(dump, description="description")
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "description",
            Ref("description"),
            False,
        )
        if "description" not in schema.definitions:
            schema.definitions["description"] = {
                "type": "string",
            }
        return schema


class HasMediaType(LinkedDataDumpable):
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
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(schema, "mediaType", MediaTypeSchema(), False)
        return schema


class HasLocale(Localized, LinkedDataDumpable):
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
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        properties = cast(DumpMapping[Dump], schema.schema.setdefault("properties", {}))
        properties["locale"] = LocaleSchema().embed(schema)
        return schema


@final
class Link(HasMediaType, HasLocale, Described, LinkedDataDumpable):
    """
    An external link.
    """

    #: The link's absolute URL
    url: str
    #: The link's `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.
    relationship: str | None
    #: The link's human-readable label.
    label = StaticTranslationsLocalizableAttr("label")

    def __init__(
        self,
        url: str,
        *,
        relationship: str | None = None,
        label: ShorthandStaticTranslations | None = None,
        description: str | None = None,
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
        dump["$ref"] = project.static_url_generator.generate(
            "schema.json#/definitions/link", absolute=True
        )
        dump["url"] = self.url
        if self.label:
            dump["label"] = await self.label.dump_linked_data(project)
        if self.relationship is not None:
            dump["relationship"] = self.relationship
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        return LinkSchema()


class LinkSchema(Schema):
    """
    A JSON Schema for :py:class:`betty.ancestry.Link`.
    """

    def __init__(self):
        super().__init__(name="link")
        add_json_ld(self)
        add_property(
            self,
            "url",
            Schema(
                schema={
                    "type": "string",
                    "format": "uri",
                    "description": "The full URL to the other resource.",
                }
            ),
        )
        add_property(
            self,
            "relationship",
            Schema(
                schema={
                    "type": "string",
                    "description": "The relationship between this resource and the link target (https://en.wikipedia.org/wiki/Link_relation).",
                }
            ),
            False,
        )
        add_property(
            self,
            "label",
            StaticTranslationsLocalizableSchema(),
            False,
        )


class LinkCollectionSchema(ArraySchema):
    """
    A JSON Schema for :py:class:`betty.ancestry.Link` collections.
    """

    def __init__(self):
        super().__init__(name="linkCollection", items_schema=LinkSchema())


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
                    media_type=MediaType("application/ld+json"),
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
                                locale=locale_configuration.locale,
                            ),
                            relationship="alternate",
                            media_type=MediaType("text/html"),
                            locale=locale_configuration.locale,
                        )
                        for locale_configuration in project.configuration.locales
                    ),
                )

        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(schema, "links", LinkCollectionSchema())
        return schema


@final
class Note(UserFacingEntity, HasPrivacy, HasLinks, Entity):
    """
    A note is a bit of textual information that can be associated with another entity.
    """

    #: The entity the note belongs to.
    entity = ManyToOne["Note", "HasNotes"](
        "betty.ancestry:Note", "entity", "betty.ancestry:HasNotes", "notes"
    )

    def __init__(
        self,
        text: str,
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
        self._text = text
        if entity is not None:
            self.entity = entity

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "note"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Note")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Notes")  # pragma: no cover

    @property
    def text(self) -> str:
        """
        The note's human-readable text.
        """
        return self._text

    @override
    @property
    def label(self) -> Localizable:
        return plain(self.text)

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        if self.public:
            dump["text"] = self.text
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "text",
            Schema(schema={"type": "string", "title": "The human-readable note text."}),
            False,
        )
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
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(schema, "notes", Ref("noteEntityCollection"))
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
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(schema, "citations", Ref("citationEntityCollection"))
        return schema


@final
class File(
    Described,
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
        description: str | None = None,
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
    def plugin_id(cls) -> str:
        return "file"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("File")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Files")  # pragma: no cover

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
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "entities",
            ArraySchema(Schema(schema={"type": "string", "format": "uri"})),
        )
        return schema


class FileReference(Entity):
    """
    A reference between :py:class:`betty.ancestry.HasFileReferences` and betty.ancestry.File.

    This reference holds additional information specific to the relationship between the two entities.
    """

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
    def plugin_id(cls) -> MachineName:
        return "file-reference"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("File reference")

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
    Dated, HasFileReferences, HasNotes, HasLinks, HasPrivacy, UserFacingEntity, Entity
):
    """
    A source of information.
    """

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

    def __init__(
        self,
        name: str | None = None,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        author: str | None = None,
        publisher: str | None = None,
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
        self.name = name
        self.author = author
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
    def plugin_id(cls) -> str:
        return "source"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Source")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Sources")  # pragma: no cover

    @override
    @property
    def label(self) -> Localizable:
        return plain(self.name) if self.name else super().label

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
            if self.name is not None:
                dump_context(dump, name="name")
                dump["name"] = self.name
            if self.author is not None:
                dump["author"] = self.author
            if self.publisher is not None:
                dump["publisher"] = self.publisher
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "name",
            Schema(
                schema={
                    "type": "string",
                }
            ),
            False,
        )
        add_property(
            schema,
            "author",
            Schema(
                schema={
                    "type": "string",
                }
            ),
            False,
        )
        add_property(
            schema,
            "publisher",
            Schema(
                schema={
                    "type": "string",
                }
            ),
            False,
        )
        add_property(
            schema,
            "contains",
            ArraySchema(
                Schema(
                    schema={
                        "type": "string",
                        "format": "uri",
                    }
                )
            ),
        )
        add_property(
            schema,
            "citations",
            Ref("citationEntityCollection"),
        )
        add_property(
            schema,
            "containedBy",
            Schema(
                schema={
                    "type": "string",
                    "format": "uri",
                }
            ),
            False,
        )
        return schema


@final
class Citation(Dated, HasFileReferences, HasPrivacy, HasLinks, UserFacingEntity):
    """
    A citation (a reference to a source).
    """

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

    def __init__(
        self,
        *,
        id: str | None = None,  # noqa A002  # noqa A002
        facts: Iterable[HasCitations & Entity] | None = None,
        source: Source | None = None,
        location: Localizable | None = None,
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
    def plugin_id(cls) -> str:
        return "citation"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Citation")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Citations")  # pragma: no cover

    @override
    @property
    def label(self) -> Localizable:
        return self.location or static("")

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
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema, "source", Schema(schema={"type": "string", "format": "uri"}), False
        )
        add_property(
            schema,
            "facts",
            ArraySchema(
                items_schema=Schema(schema={"type": "string", "format": "uri"})
            ),
        )
        return schema


@final
class PlaceName(HasLocale, Dated, LinkedDataDumpable):
    """
    A place name.

    A name has a locale and a date during which the name was in use.
    """

    def __init__(
        self,
        name: str,
        *,
        locale: str = UNDETERMINED_LOCALE,
        date: Datey | None = None,
    ):
        super().__init__(
            date=date,
            locale=locale,
        )
        self._name = name

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented  # pragma: no cover
        return self._name == other._name and self.locale == other.locale

    @override  # type: ignore[callable-functiontype]
    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, name=self.name, locale=self.locale)

    @override
    def __str__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        """
        The human-readable name.
        """
        return self._name

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["name"] = self.name
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = Schema(name="placeName")
        add_property(schema, "name", Schema(schema={"type": "string"}))
        return schema


@final
class Enclosure(Dated, HasCitations, Entity):
    """
    The enclosure of one place by another.

    Enclosures describe the outer (```enclosed_by`) and inner(``encloses``) places, and their relationship.
    """

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
    def plugin_id(cls) -> str:
        return "enclosure"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Enclosure")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Enclosures")  # pragma: no cover


@final
class Place(
    HasLinks, HasFileReferences, HasNotes, HasPrivacy, UserFacingEntity, Entity
):
    """
    A place.

    A place is a physical location on earth. It may be identifiable by GPS coordinates only, or
    be a well-known city, with names in many languages, imagery, and its own Wikipedia page, or
    any type of place in between.
    """

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
        names: MutableSequence[PlaceName] | None = None,
        events: Iterable[Event] | None = None,
        enclosed_by: Iterable[Enclosure] | None = None,
        encloses: Iterable[Enclosure] | None = None,
        notes: Iterable[Note] | None = None,
        coordinates: Point | None = None,
        links: MutableSequence[Link] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
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
    def plugin_id(cls) -> str:
        return "place"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Place")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Places")  # pragma: no cover

    @property
    def names(self) -> MutableSequence[PlaceName]:
        """
        The place's names.
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
        # @todo Negotiate this by locale and date.
        with suppress(IndexError):
            return plain(self.names[0].name)
        return super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(
            dump,
            names="name",
            events="event",
            enclosedBy="containedInPlace",
            encloses="containsPlace",
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
            dump_context(dump, coordinates="geo")
            dump_context(
                dump["coordinates"],  # type: ignore[arg-type]
                latitude="latitude",
            )
            dump_context(
                dump["coordinates"],  # type: ignore[arg-type]
                longitude="longitude",
            )
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "names",
            ArraySchema(await PlaceName.linked_data_schema(project)),
        )
        add_property(
            schema,
            "enclosedBy",
            Ref("placeEntityCollection"),
            False,
        )
        add_property(
            schema,
            "encloses",
            Ref("placeEntityCollection"),
        )
        coordinate_schema = Schema(
            schema={
                "type": "number",
            }
        )
        coordinates_schema = Schema(
            schema={
                "type": "object",
                "additionalProperties": False,
            }
        )
        add_property(coordinates_schema, "latitude", coordinate_schema, False)
        add_property(coordinates_schema, "longitude", coordinate_schema, False)
        add_json_ld(coordinates_schema)
        add_property(schema, "coordinates", coordinates_schema, False)
        add_property(
            schema,
            "events",
            Ref("eventEntityCollection"),
        )
        return schema


@final
class Presence(HasPrivacy, Entity):
    """
    The presence of a :py:class:`betty.ancestry.Person` at an :py:class:`betty.ancestry.Event`.
    """

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
    def plugin_id(cls) -> str:
        return "presence"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Presence")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Presences")  # pragma: no cover

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
    Dated,
    HasFileReferences,
    HasCitations,
    HasNotes,
    Described,
    HasPrivacy,
    HasLinks,
    UserFacingEntity,
):
    """
    An event that took place.
    """

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
        description: str | None = None,
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
    def plugin_id(cls) -> str:
        return "event"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Event")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Events")  # pragma: no cover

    @property
    def event_type(self) -> EventType:
        """
        The type of event.
        """
        return self._event_type

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(dump, presences="performer")
        dump["@type"] = "https://schema.org/Event"
        dump["type"] = self.event_type.plugin_id()
        dump["eventAttendanceMode"] = "https://schema.org/OfflineEventAttendanceMode"
        dump["eventStatus"] = "https://schema.org/EventScheduled"
        dump["presences"] = presences = []
        if self.date is not None and self.public:
            await self.date.datey_dump_linked_data(
                dump["date"],  # type: ignore[arg-type]
                "startDate",
                "endDate",
            )
        for presence in self.presences:
            if presence.person and not isinstance(
                presence.person.id, GeneratedEntityId
            ):
                presences.append(self._dump_event_presence(presence, project))
        if self.place is not None and not isinstance(self.place.id, GeneratedEntityId):
            dump["place"] = project.static_url_generator.generate(
                f"/place/{quote(self.place.id)}/index.json"
            )
            dump_context(dump, place="location")
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
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "type",
            Schema(
                schema={
                    "type": "string",
                }
            ),
        )
        add_property(
            schema,
            "place",
            Schema(
                schema={
                    "type": "string",
                    "format": "uri",
                }
            ),
            False,
        )
        add_property(
            schema,
            "presences",
            ArraySchema(_EventPresenceSchema()),
        )
        add_property(
            schema,
            "eventStatus",
            Schema(
                schema={
                    "type": "string",
                }
            ),
        )
        add_property(
            schema,
            "eventAttendanceMode",
            Schema(
                schema={
                    "type": "string",
                }
            ),
        )
        return schema


class _EventPresenceSchema(Schema):
    """
    A schema for the :py:class:`betty.ancestry.Presence` associations on a :py:class:`betty.ancestry.Event`.
    """

    def __init__(self):
        super().__init__()
        self.schema["type"] = "object"
        self.schema["additionalProperties"] = False
        add_property(self, "role", PresenceRoleSchema(), False)
        add_property(
            self,
            "person",
            Schema(
                schema={
                    "type": "string",
                    "format": "uri",
                }
            ),
        )
        add_json_ld(self)


@final
class PersonName(HasLocale, HasCitations, HasPrivacy, Entity):
    """
    A name for a :py:class:`betty.ancestry.Person`.
    """

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
    def plugin_id(cls) -> str:
        return "person-name"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Person name")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Person names")  # pragma: no cover

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
                dump_context(dump, individual="givenName")
                dump["individual"] = self.individual
            if self.affiliation is not None:
                dump_context(dump, affiliation="familyName")
                dump["affiliation"] = self.affiliation
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "individual",
            Schema(
                schema={
                    "type": "string",
                }
            ),
            False,
        )
        add_property(
            schema,
            "affiliation",
            Schema(
                schema={
                    "type": "string",
                }
            ),
            False,
        )
        return schema


@final
class Person(
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

    @override
    @classmethod
    def plugin_id(cls) -> str:
        return "person"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return _("Person")  # pragma: no cover

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("People")  # pragma: no cover

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
            names="name",
            parents="parent",
            children="child",
            siblings="sibling",
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
        dump_context(dump, event="performerIn")
        if presence.public:
            dump["role"] = presence.role.plugin_id()
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Schema:
        schema = await super().linked_data_schema(project)
        add_property(
            schema,
            "names",
            ArraySchema(await PersonName.linked_data_schema(project)),
        )
        add_property(
            schema,
            "parents",
            Ref("personEntityCollection"),
        )
        add_property(
            schema,
            "children",
            Ref("personEntityCollection"),
        )
        add_property(
            schema,
            "siblings",
            Ref("personEntityCollection"),
        )
        add_property(
            schema,
            "presences",
            ArraySchema(_PersonPresenceSchema()),
        )
        return schema


class _PersonPresenceSchema(Schema):
    """
    A schema for the :py:class:`betty.ancestry.Presence` associations on a :py:class:`betty.ancestry.Person`.
    """

    def __init__(self):
        super().__init__()
        self.schema["type"] = "object"
        self.schema["additionalProperties"] = False
        add_property(self, "role", PresenceRoleSchema(), False)
        add_property(
            self,
            "event",
            Schema(
                schema={
                    "type": "string",
                    "format": "uri",
                }
            ),
        )
        add_json_ld(self)


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
