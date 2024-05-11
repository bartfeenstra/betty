"""
Provide Betty's main data model.
"""

from __future__ import annotations

from collections.abc import MutableSequence, Iterator
from contextlib import suppress
from enum import Enum
from pathlib import Path
from reprlib import recursive_repr
from typing import Iterable, Any, TYPE_CHECKING
from urllib.parse import quote

from geopy import Point

from betty.classtools import repr_instance
from betty.json.linked_data import (
    LinkedDataDumpable,
    dump_context,
    dump_link,
    add_json_ld,
)
from betty.json.schema import add_property, ref_json_schema
from betty.locale import Localized, Datey, Str, Localizable, ref_datey
from betty.media_type import MediaType
from betty.model import (
    many_to_many,
    Entity,
    one_to_many,
    many_to_one,
    many_to_one_to_many,
    MultipleTypesEntityCollection,
    EntityCollection,
    UserFacingEntity,
    EntityTypeAssociationRegistry,
    GeneratedEntityId,
    get_entity_type_name,
)
from betty.model.event_type import EventType, UnknownEventType
from betty.serde.dump import DictDump, Dump, dump_default
from betty.string import camel_case_to_kebab_case
from betty.warnings import deprecated

if TYPE_CHECKING:
    from betty.app import App


class Privacy(Enum):
    PUBLIC = 1
    PRIVATE = 2
    UNDETERMINED = 3


class HasPrivacy(LinkedDataDumpable):
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
        return self._privacy

    def _get_effective_privacy(self) -> Privacy:
        return self.own_privacy

    @property
    def privacy(self) -> Privacy:
        return self._get_effective_privacy()

    @privacy.setter
    def privacy(self, privacy: Privacy) -> None:
        self._privacy = privacy

    @privacy.deleter
    def privacy(self) -> None:
        self.privacy = Privacy.UNDETERMINED

    @property
    def private(self) -> bool:
        return self.privacy is Privacy.PRIVATE

    @private.setter
    def private(self, private: True) -> None:
        self.privacy = Privacy.PRIVATE

    @property
    def public(self) -> bool:
        # Undetermined privacy defaults to public.
        return self.privacy is not Privacy.PRIVATE

    @public.setter
    def public(self, public: True) -> None:
        self.privacy = Privacy.PUBLIC

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["private"] = self.private
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "private",
            {
                "$ref": "#/definitions/privacy",
            },
        )
        definitions = dump_default(schema, "definitions", dict)
        if "privacy" not in definitions:
            definitions["privacy"] = {
                "type": "boolean",
                "description": "Whether this entity is private (true), or public (false).",
            }
        return schema


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
    def __init__(
        self,
        *args: Any,
        date: Datey | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.date = date

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        if self.date and is_public(self):
            dump["date"] = await self.date.dump_linked_data(app)
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        schema["type"] = "object"
        schema["additionalProperties"] = False
        add_property(schema, "date", await ref_datey(schema, app), False)
        return schema


class Described(LinkedDataDumpable):
    def __init__(
        self,
        *args: Any,
        description: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.description = description

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        if self.description is not None:
            dump["description"] = self.description
            dump_context(dump, description="description")
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "description",
            {
                "$ref": "#/definitions/description",
            },
            False,
        )
        definitions = dump_default(schema, "definitions", dict)
        if "description" not in definitions:
            definitions["description"] = {
                "type": "string",
            }
        return schema


class HasMediaType(LinkedDataDumpable):
    def __init__(
        self,
        *args: Any,
        media_type: MediaType | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.media_type = media_type

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        if is_public(self):
            if self.media_type is not None:
                dump["mediaType"] = str(self.media_type)
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(schema, "mediaType", ref_media_type(schema), False)
        return schema


def ref_media_type(root_schema: DictDump[Dump]) -> DictDump[Dump]:
    """
    Reference the MediaType schema.
    """
    definitions = dump_default(root_schema, "definitions", dict)
    if "mediaType" not in definitions:
        definitions["mediaType"] = {
            "type": "string",
            "description": "An IANA media type (https://www.iana.org/assignments/media-types/media-types.xhtml).",
        }
    return {
        "$ref": "#/definitions/mediaType",
    }


class Link(HasMediaType, Localized, Described, LinkedDataDumpable):
    url: str
    relationship: str | None
    label: str | None

    def __init__(
        self,
        url: str,
        *,
        relationship: str | None = None,
        label: str | None = None,
        description: str | None = None,
        media_type: MediaType | None = None,
        locale: str | None = None,
    ):
        super().__init__(
            media_type=media_type,
            description=description,
            locale=locale,
        )
        self.url = url
        self.label = label
        self.relationship = relationship

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["$schema"] = app.static_url_generator.generate(
            "schema.json#/definitions/link", absolute=True
        )
        dump["url"] = self.url
        if self.label is not None:
            dump["label"] = self.label
        if self.relationship is not None:
            dump["relationship"] = self.relationship
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        schema["type"] = "object"
        schema["additionalProperties"] = False
        add_json_ld(schema)
        add_property(schema, "$schema", ref_json_schema(schema))
        add_property(
            schema,
            "label",
            {
                "type": "string",
                "description": "The human-readable label, or link text.",
            },
            False,
        )
        add_property(
            schema,
            "url",
            {
                "type": "string",
                "format": "uri",
                "description": "The full URL to the other resource.",
            },
        )
        add_property(
            schema,
            "relationship",
            {
                "type": "string",
                "description": "The relationship between this resource and the link target (https://en.wikipedia.org/wiki/Link_relation).",
            },
            False,
        )
        return schema


async def ref_link(root_schema: DictDump[Dump], app: App) -> DictDump[Dump]:
    """
    Reference the Link schema.
    """
    definitions = dump_default(root_schema, "definitions", dict)
    if "link" not in definitions:
        definitions["link"] = await Link.linked_data_schema(app)
    return {
        "$ref": "#/definitions/link",
    }


async def ref_link_collection(root_schema: DictDump[Dump], app: App) -> DictDump[Dump]:
    """
    Reference the schema for a collection of Link instances.
    """
    definitions = dump_default(root_schema, "definitions", dict)
    if "linkCollection" not in definitions:
        definitions["linkCollection"] = {
            "type": "array",
            "items": await ref_link(root_schema, app),
        }
    return {
        "$ref": "#/definitions/linkCollection",
    }


class HasLinks(LinkedDataDumpable):
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
        return self._links

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        await dump_link(
            dump,
            app,
            *(self.links if is_public(self) else ()),
        )
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(schema, "links", await ref_link_collection(schema, app))
        return schema


class HasLinksEntity(HasLinks):
    async def dump_linked_data(  # type: ignore[misc]
        self: HasLinksEntity & Entity,
        app: App,
    ) -> DictDump[Dump]:
        dump: DictDump[Dump] = await super().dump_linked_data(app)  # type: ignore[misc]

        if not isinstance(self.id, GeneratedEntityId):
            await dump_link(
                dump,
                app,
                Link(
                    app.static_url_generator.generate(
                        f"/{camel_case_to_kebab_case(get_entity_type_name(self.type))}/{self.id}/index.json"
                    ),
                    relationship="canonical",
                    media_type=MediaType("application/ld+json"),
                ),
            )
            if is_public(self):
                await dump_link(
                    dump,
                    app,
                    *(
                        Link(
                            app.url_generator.generate(
                                self, media_type="text/html", locale=locale
                            ),
                            relationship="alternate",
                            media_type=MediaType("text/html"),
                            locale=locale,
                        )
                        for locale in app.project.configuration.locales
                    ),
                )

        return dump


@many_to_one("entity", "betty.model.ancestry.HasNotes", "notes")
class Note(UserFacingEntity, HasPrivacy, HasLinksEntity, Entity):
    entity: HasNotes

    def __init__(
        self,
        text: str,
        *,
        id: str | None = None,
        entity: HasNotes | None = None,
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

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Note")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Notes")  # pragma: no cover

    @property
    def text(self) -> str:
        return self._text

    @property
    def label(self) -> Str:
        return Str.plain(self.text)

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["@type"] = "https://schema.org/Thing"
        if self.public:
            dump["text"] = self.text
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(schema, "text", {"type": "string"}, False)
        return schema


@one_to_many("notes", "betty.model.ancestry.Note", "entity")
class HasNotes(LinkedDataDumpable):
    def __init__(  # type: ignore[misc]
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
            self.notes = notes  # type: ignore[assignment]

    @property
    def notes(self) -> EntityCollection[Note]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @notes.setter
    def notes(self, notes: Iterable[Note]) -> None:
        pass  # pragma: no cover

    @notes.deleter
    def notes(self) -> None:
        pass  # pragma: no cover

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["notes"] = [
            app.static_url_generator.generate(f"/note/{quote(note.id)}/index.json")
            for note in self.notes
            if not isinstance(note.id, GeneratedEntityId)
        ]
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "notes",
            {
                "$ref": "#/definitions/entity/noteCollection",
            },
        )
        return schema


@many_to_many("citations", "betty.model.ancestry.Citation", "facts")
class HasCitations(LinkedDataDumpable):
    def __init__(  # type: ignore[misc]
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
            self.citations = citations  # type: ignore[assignment]

    @property
    def citations(self) -> EntityCollection[Citation]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @citations.setter
    def citations(self, citations: Iterable[Citation]) -> None:
        pass  # pragma: no cover

    @citations.deleter
    def citations(self) -> None:
        pass  # pragma: no cover

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["citations"] = [
            app.static_url_generator.generate(
                f"/citation/{quote(citation.id)}/index.json"
            )
            for citation in self.citations
            if not isinstance(citation.id, GeneratedEntityId)
        ]
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "citations",
            {
                "$ref": "#/definitions/entity/citationCollection",
            },
        )
        return schema


@many_to_many("entities", "betty.model.ancestry.HasFiles", "files")
class File(
    Described,
    HasPrivacy,
    HasLinksEntity,
    HasMediaType,
    HasNotes,
    HasCitations,
    UserFacingEntity,
    Entity,
):
    def __init__(
        self,
        path: Path,
        *,
        id: str | None = None,
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

    @property
    def entities(self) -> EntityCollection[Entity]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @entities.setter
    def entities(self, entities: Iterable[Entity]) -> None:
        pass  # pragma: no cover

    @entities.deleter
    def entities(self) -> None:
        pass  # pragma: no cover

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("File")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Files")  # pragma: no cover

    @property
    def path(self) -> Path:
        return self._path

    @property
    def label(self) -> Str:
        return Str.plain(self.description) if self.description else super().label

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["entities"] = [
            app.static_url_generator.generate(
                f"/{camel_case_to_kebab_case(get_entity_type_name(entity))}/{quote(entity.id)}/index.json"
            )
            for entity in self.entities
            if not isinstance(entity.id, GeneratedEntityId)
        ]
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "entities",
            {"type": "array", "items": {"type": "string", "format": "uri"}},
        )
        return schema


@many_to_many("files", "betty.model.ancestry.File", "entities")
class HasFiles:
    def __init__(  # type: ignore[misc]
        self: HasFiles & Entity,
        *args: Any,
        files: Iterable[File] | None = None,
        **kwargs: Any,
    ):
        super().__init__(  # type: ignore[misc]
            *args,
            **kwargs,
        )
        if files is not None:
            self.files = files  # type: ignore[assignment]

    @property
    def files(self) -> EntityCollection[File]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @files.setter
    def files(self, files: Iterable[File]) -> None:
        pass  # pragma: no cover

    @files.deleter
    def files(self) -> None:
        pass  # pragma: no cover

    @property
    def associated_files(self) -> Iterable[File]:
        return self.files


@many_to_one("contained_by", "betty.model.ancestry.Source", "contains")
@one_to_many("contains", "betty.model.ancestry.Source", "contained_by")
@one_to_many("citations", "betty.model.ancestry.Citation", "source")
class Source(
    Dated, HasFiles, HasNotes, HasLinksEntity, HasPrivacy, UserFacingEntity, Entity
):
    contained_by: Source | None

    def __init__(
        self,
        name: str | None = None,
        *,
        id: str | None = None,
        author: str | None = None,
        publisher: str | None = None,
        contained_by: Source | None = None,
        contains: Iterable[Source] | None = None,
        notes: Iterable[Note] | None = None,
        date: Datey | None = None,
        files: Iterable[File] | None = None,
        links: MutableSequence[Link] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            notes=notes,
            date=date,
            files=files,
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
            self.contains = contains  # type: ignore[assignment]

    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.contained_by:
            return merge_privacies(privacy, self.contained_by.privacy)
        return privacy

    @property
    def contains(self) -> EntityCollection[Source]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @contains.setter
    def contains(self, contains: Iterable[Source]) -> None:
        pass  # pragma: no cover

    @contains.deleter
    def contains(self) -> None:
        pass  # pragma: no cover

    @property
    def citations(self) -> EntityCollection[Citation]:  # type: ignore[empty-body]
        pass

    @citations.setter
    def citations(self, citations: Iterable[Citation]) -> None:
        pass  # pragma: no cover

    @citations.deleter
    def citations(self) -> None:
        pass  # pragma: no cover

    @property
    def walk_contains(self) -> Iterator[Source]:
        for source in self.contains:
            yield source
            yield from source.contains

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Source")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Sources")  # pragma: no cover

    @property
    def label(self) -> Str:
        return Str.plain(self.name) if self.name else super().label

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["@type"] = "https://schema.org/Thing"
        dump["contains"] = [
            app.static_url_generator.generate(
                f"/source/{quote(contained.id)}/index.json"
            )
            for contained in self.contains
            if not isinstance(contained.id, GeneratedEntityId)
        ]
        dump["citations"] = [
            app.static_url_generator.generate(
                f"/citation/{quote(citation.id)}/index.json"
            )
            for citation in self.citations
            if not isinstance(citation.id, GeneratedEntityId)
        ]
        if self.contained_by is not None and not isinstance(
            self.contained_by.id, GeneratedEntityId
        ):
            dump["containedBy"] = app.static_url_generator.generate(
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

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "name",
            {
                "type": "string",
            },
            False,
        )
        add_property(
            schema,
            "author",
            {
                "type": "string",
            },
            False,
        )
        add_property(
            schema,
            "publisher",
            {
                "type": "string",
            },
            False,
        )
        add_property(
            schema,
            "contains",
            {
                "type": "array",
                "items": {
                    "type": "string",
                    "format": "uri",
                },
            },
        )
        add_property(
            schema,
            "citations",
            {
                "$ref": "#/definitions/entity/citationCollection",
            },
        )
        add_property(
            schema,
            "containedBy",
            {
                "type": "string",
                "format": "uri",
            },
            False,
        )
        return schema


@deprecated(
    f"This class is deprecated as of Betty 0.3.2, and will be removed in Betty 0.4.x. No direct replacement is available. Instead, set the privacy for {Source} entities accordingly."
)
class AnonymousSource(Source):
    @property  # type: ignore[override]
    def name(self) -> str:
        return "private"

    @name.setter
    def name(self, _) -> None:
        # This is a no-op as the name is 'hardcoded'.
        pass  # pragma: no cover

    @name.deleter
    def name(self) -> None:
        # This is a no-op as the name is 'hardcoded'.
        pass  # pragma: no cover


@many_to_many("facts", "betty.model.ancestry.HasCitations", "citations")
@many_to_one("source", "betty.model.ancestry.Source", "citations")
class Citation(Dated, HasFiles, HasPrivacy, HasLinksEntity, UserFacingEntity, Entity):
    def __init__(
        self,
        *,
        id: str | None = None,
        facts: Iterable[HasCitations] | None = None,
        source: Source | None = None,
        location: Str | None = None,
        date: Datey | None = None,
        files: Iterable[File] | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            id,
            date=date,
            files=files,
            privacy=privacy,
            public=public,
            private=private,
        )
        if facts is not None:
            self.facts = facts  # type: ignore[assignment]
        self.location = location
        self.source = source

    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.source:
            return merge_privacies(privacy, self.source.privacy)
        return privacy

    @property
    def facts(self) -> EntityCollection[HasCitations & Entity]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @facts.setter
    def facts(self, facts: Iterable[HasCitations & Entity]) -> None:
        pass  # pragma: no cover

    @facts.deleter
    def facts(self) -> None:
        pass  # pragma: no cover

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Citation")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Citations")  # pragma: no cover

    @property
    def label(self) -> Str:
        return self.location or Str.plain("")

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["@type"] = "https://schema.org/Thing"
        dump["facts"] = [
            app.static_url_generator.generate(
                f"/{camel_case_to_kebab_case(get_entity_type_name(fact))}/{quote(fact.id)}/index.json"
            )
            for fact in self.facts
            if not isinstance(fact.id, GeneratedEntityId)
        ]
        if self.source is not None and not isinstance(
            self.source.id, GeneratedEntityId
        ):
            dump["source"] = app.static_url_generator.generate(
                f"/source/{quote(self.source.id)}/index.json"
            )
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(schema, "source", {"type": "string", "format": "uri"}, False)
        add_property(
            schema,
            "facts",
            {"type": "array", "items": {"type": "string", "format": "uri"}},
        )
        return schema


@deprecated(
    f"This class is deprecated as of Betty 0.3.2, and will be removed in Betty 0.4.x. No direct replacement is available. Instead, set the privacy for {Citation} entities accordingly."
)
class AnonymousCitation(Citation):
    @property  # type: ignore[override]
    def location(self) -> Str:
        return Str._(
            "private (in order to protect people's privacy)"
        )  # pragma: no cover

    @location.setter
    def location(self, _) -> None:
        # This is a no-op as the location is 'hardcoded'.
        pass  # pragma: no cover

    @location.deleter
    def location(self) -> None:
        # This is a no-op as the location is 'hardcoded'.
        pass  # pragma: no cover


class PlaceName(Localized, Dated, LinkedDataDumpable):
    def __init__(
        self,
        name: str,
        *,
        locale: str | None = None,
        date: Datey | None = None,
    ):
        super().__init__(
            date=date,
            locale=locale,
        )
        self._name = name

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented  # pragma: no cover
        return self._name == other._name and self.locale == other.locale

    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, name=self.name, locale=self.locale)

    def __str__(self) -> str:
        return self._name

    @property
    def name(self) -> str:
        return self._name

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump["name"] = self.name
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(schema, "name", {"type": "string"})
        return schema


@many_to_one_to_many(
    "betty.model.ancestry.Place",
    "enclosed_by",
    "encloses",
    "enclosed_by",
    "betty.model.ancestry.Place",
    "encloses",
)
class Enclosure(Dated, HasCitations, Entity):
    encloses: Place | None
    enclosed_by: Place | None

    def __init__(
        self,
        encloses: Place | None = None,
        enclosed_by: Place | None = None,
    ):
        super().__init__()
        self.encloses = encloses
        self.enclosed_by = enclosed_by

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Enclosure")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Enclosures")  # pragma: no cover


@one_to_many("events", "betty.model.ancestry.Event", "place")
@one_to_many("enclosed_by", "betty.model.ancestry.Enclosure", "encloses")
@one_to_many("encloses", "betty.model.ancestry.Enclosure", "enclosed_by")
class Place(HasLinksEntity, HasFiles, HasNotes, HasPrivacy, UserFacingEntity, Entity):
    def __init__(
        self,
        *,
        id: str | None = None,
        names: list[PlaceName] | None = None,
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
            self.events = events  # type: ignore[assignment]
        if enclosed_by is not None:
            self.enclosed_by = enclosed_by  # type: ignore[assignment]
        if encloses is not None:
            self.encloses = encloses  # type: ignore[assignment]

    @property
    def enclosed_by(self) -> EntityCollection[Enclosure]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @enclosed_by.setter
    def enclosed_by(self, enclosed_by: Iterable[Enclosure]) -> None:
        pass  # pragma: no cover

    @enclosed_by.deleter
    def enclosed_by(self) -> None:
        pass  # pragma: no cover

    @property
    def encloses(self) -> EntityCollection[Enclosure]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @encloses.setter
    def encloses(self, encloses: Iterable[Enclosure]) -> None:
        pass  # pragma: no cover

    @encloses.deleter
    def encloses(self) -> None:
        pass  # pragma: no cover

    @property
    def events(self) -> EntityCollection[Event]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @events.setter
    def events(self, events: Iterable[Event]) -> None:
        pass  # pragma: no cover

    @events.deleter
    def events(self) -> None:
        pass  # pragma: no cover

    @property
    def walk_encloses(self) -> Iterator[Enclosure]:
        for enclosure in self.encloses:
            yield enclosure
            if enclosure.encloses is not None:
                yield from enclosure.encloses.walk_encloses

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Place")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Places")  # pragma: no cover

    @property
    def names(self) -> list[PlaceName]:
        return self._names

    @property
    def coordinates(self) -> Point | None:
        return self._coordinates

    @coordinates.setter
    def coordinates(self, coordinates: Point):
        self._coordinates = coordinates

    @property
    def label(self) -> Str:
        # @todo Negotiate this by locale and date.
        with suppress(IndexError):
            return Str.plain(self.names[0].name)
        return super().label

    @property
    def associated_files(self) -> Iterable[File]:
        yield from self.files
        for event in self.events:
            yield from event.files

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump_context(
            dump,
            names="name",
            events="event",
            enclosedBy="containedInPlace",
            encloses="containsPlace",
        )
        dump["@type"] = "https://schema.org/Place"
        dump["names"] = [await name.dump_linked_data(app) for name in self.names]
        dump["events"] = [
            app.static_url_generator.generate(f"/event/{quote(event.id)}/index.json")
            for event in self.events
            if not isinstance(event.id, GeneratedEntityId)
        ]
        dump["enclosedBy"] = [
            app.static_url_generator.generate(
                f"/place/{quote(enclosure.enclosed_by.id)}/index.json"
            )
            for enclosure in self.enclosed_by
            if enclosure.enclosed_by is not None
            and not isinstance(enclosure.enclosed_by.id, GeneratedEntityId)
        ]
        dump["encloses"] = [
            app.static_url_generator.generate(
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

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "names",
            {
                "type": "array",
                "items": await PlaceName.linked_data_schema(app),
            },
        )
        add_property(
            schema,
            "enclosedBy",
            {"$ref": "#/definitions/entity/placeCollection"},
            False,
        )
        add_property(
            schema, "encloses", {"$ref": "#/definitions/entity/placeCollection"}
        )
        coordinate_schema: DictDump[Dump] = {
            "type": "number",
        }
        coordinates_schema: DictDump[Dump] = {
            "type": "object",
            "additionalProperties": False,
        }
        add_property(coordinates_schema, "latitude", coordinate_schema, False)
        add_property(coordinates_schema, "longitude", coordinate_schema, False)
        add_json_ld(coordinates_schema, schema)
        add_property(schema, "coordinates", coordinates_schema, False)
        add_property(schema, "events", {"$ref": "#/definitions/entity/eventCollection"})
        return schema


class PresenceRole:
    @classmethod
    def name(cls) -> str:
        raise NotImplementedError(repr(cls))

    @property
    def label(self) -> Str:
        raise NotImplementedError(repr(self))


def ref_role(root_schema: DictDump[Dump]) -> DictDump[Dump]:
    """
    Reference the PresenceRole schema.
    """
    definitions = dump_default(root_schema, "definitions", dict)
    if "role" not in definitions:
        definitions["role"] = {
            "type": "string",
            "description": "A person's role in an event.",
        }
    return {
        "$ref": "#/definitions/role",
    }


class Subject(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return "subject"

    @property
    def label(self) -> Str:
        return Str._("Subject")  # pragma: no cover


class Witness(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return "witness"  # pragma: no cover

    @property
    def label(self) -> Str:
        return Str._("Witness")  # pragma: no cover


class Beneficiary(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return "beneficiary"  # pragma: no cover

    @property
    def label(self) -> Str:
        return Str._("Beneficiary")  # pragma: no cover


class Attendee(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return "attendee"  # pragma: no cover

    @property
    def label(self) -> Str:
        return Str._("Attendee")  # pragma: no cover


class Speaker(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return "speaker"  # pragma: no cover

    @property
    def label(self) -> Str:
        return Str._("Speaker")  # pragma: no cover


class Celebrant(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return "celebrant"  # pragma: no cover

    @property
    def label(self) -> Str:
        return Str._("Celebrant")  # pragma: no cover


class Organizer(PresenceRole):
    @classmethod
    def name(cls) -> str:
        return "organizer"  # pragma: no cover

    @property
    def label(self) -> Str:
        return Str._("Organizer")  # pragma: no cover


@many_to_one_to_many(
    "betty.model.ancestry.Person",
    "presences",
    "person",
    "event",
    "betty.model.ancestry.Event",
    "presences",
)
class Presence(HasPrivacy, Entity):
    person: Person | None
    event: Event | None
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

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Presence")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Presences")  # pragma: no cover

    @property
    def label(self) -> Str:
        return Str._(
            "Presence of {person} at {event}",
            person=self.person.label if self.person else Str._("Unknown"),
            event=self.event.label if self.event else Str._("Unknown"),
        )

    def _get_effective_privacy(self) -> Privacy:
        return merge_privacies(
            super()._get_effective_privacy(),
            self.person,
            self.event,
        )


@many_to_one("place", "betty.model.ancestry.Place", "events")
@one_to_many("presences", "betty.model.ancestry.Presence", "event")
class Event(
    Dated,
    HasFiles,
    HasCitations,
    HasNotes,
    Described,
    HasPrivacy,
    HasLinksEntity,
    UserFacingEntity,
    Entity,
):
    place: Place | None

    def __init__(
        self,
        *,
        id: str | None = None,
        event_type: type[EventType] = UnknownEventType,
        date: Datey | None = None,
        files: Iterable[File] | None = None,
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
            files=files,
            citations=citations,
            notes=notes,
            privacy=privacy,
            public=public,
            private=private,
            description=description,
        )
        self._event_type = event_type
        if place is not None:
            self.place = place

    @property
    def label(self) -> Str:
        format_kwargs: dict[str, str | Localizable] = {
            "event_type": self._event_type.label(),
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
            format_kwargs["subjects"] = Str.call(
                lambda localizer: ", ".join(
                    person.label.localize(localizer) for person in subjects
                )
            )
        if self.description is not None:
            format_kwargs["event_description"] = self.description

        if subjects:
            if self.description is None:
                return Str._("{event_type} of {subjects}", **format_kwargs)
            else:
                return Str._(
                    "{event_type} ({event_description}) of {subjects}", **format_kwargs
                )
        if self.description is None:
            return Str._("{event_type}", **format_kwargs)
        else:
            return Str._("{event_type} ({event_description})", **format_kwargs)

    @recursive_repr()
    def __repr__(self) -> str:
        return repr_instance(self, id=self._id, type=self._event_type)

    @property
    def presences(self) -> EntityCollection[Presence]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @presences.setter
    def presences(self, presences: Iterable[Presence]) -> None:
        pass  # pragma: no cover

    @presences.deleter
    def presences(self) -> None:
        pass  # pragma: no cover

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Event")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Events")  # pragma: no cover

    @property
    def event_type(self) -> type[EventType]:
        return self._event_type

    @property
    def associated_files(self) -> Iterable[File]:
        files = [
            *self.files,
            *[
                file
                for citation in self.citations
                for file in citation.associated_files
            ],
        ]
        # Preserve the original order.
        seen = set()
        for file in files:
            if file in seen:
                continue
            seen.add(file)
            yield file

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump_context(dump, presences="performer")
        dump["@type"] = "https://schema.org/Event"
        dump["type"] = self.event_type.name()
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
                presences.append(self._dump_event_presence(presence, app))
        if self.place is not None and not isinstance(self.place.id, GeneratedEntityId):
            dump["place"] = app.static_url_generator.generate(
                f"/place/{quote(self.place.id)}/index.json"
            )
            dump_context(dump, place="location")
        return dump

    def _dump_event_presence(self, presence: Presence, app: App) -> DictDump[Dump]:
        assert presence.person
        dump: DictDump[Dump] = {
            "@type": "https://schema.org/Person",
            "person": app.static_url_generator.generate(
                f"/person/{quote(presence.person.id)}/index.json"
            ),
        }
        if presence.public:
            dump["role"] = presence.role.name()
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "type",
            {
                "type": "string",
            },
        )
        add_property(
            schema,
            "place",
            {
                "type": "string",
                "format": "uri",
            },
            False,
        )
        presence_schema: DictDump[Dump] = {
            "type": "object",
            "additionalProperties": False,
        }
        add_property(presence_schema, "role", ref_role(schema), False)
        add_property(
            presence_schema,
            "person",
            {
                "type": "string",
                "format": "uri",
            },
        )
        add_json_ld(presence_schema, schema)
        add_property(
            schema,
            "presences",
            {
                "type": "array",
                "items": presence_schema,
            },
        )
        add_property(
            schema,
            "eventStatus",
            {
                "type": "string",
            },
        )
        add_property(
            schema,
            "eventAttendanceMode",
            {
                "type": "string",
            },
        )
        return schema


@many_to_one("person", "betty.model.ancestry.Person", "names")
class PersonName(Localized, HasCitations, HasPrivacy, Entity):
    person: Person | None

    def __init__(
        self,
        *,
        id: str | None = None,
        person: Person | None = None,
        individual: str | None = None,
        affiliation: str | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        locale: str | None = None,
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

    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if self.person:
            return merge_privacies(privacy, self.person.privacy)
        return privacy

    def __repr__(self) -> str:
        return repr_instance(
            self, id=self.id, individual=self.individual, affiliation=self.affiliation
        )

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Person name")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("Person names")  # pragma: no cover

    @property
    def individual(self) -> str | None:
        return self._individual

    @property
    def affiliation(self) -> str | None:
        return self._affiliation

    @property
    def label(self) -> Str:
        return Str._(
            "{individual_name} {affiliation_name}",
            individual_name="…" if not self.individual else self.individual,
            affiliation_name="…" if not self.affiliation else self.affiliation,
        )

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        if self.public:
            if self.individual is not None:
                dump_context(dump, individual="givenName")
                dump["individual"] = self.individual
            if self.affiliation is not None:
                dump_context(dump, affiliation="familyName")
                dump["affiliation"] = self.affiliation
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "individual",
            {
                "type": "string",
            },
            False,
        )
        add_property(
            schema,
            "affiliation",
            {
                "type": "string",
            },
            False,
        )
        return schema


@many_to_many("parents", "betty.model.ancestry.Person", "children")
@many_to_many("children", "betty.model.ancestry.Person", "parents")
@one_to_many("presences", "betty.model.ancestry.Presence", "person")
@one_to_many("names", "betty.model.ancestry.PersonName", "person")
class Person(
    HasFiles,
    HasCitations,
    HasNotes,
    HasLinksEntity,
    HasPrivacy,
    UserFacingEntity,
    Entity,
):
    def __init__(
        self,
        *,
        id: str | None = None,
        files: Iterable[File] | None = None,
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
            files=files,
            citations=citations,
            links=links,
            notes=notes,
            privacy=privacy,
            public=public,
            private=private,
        )
        if children is not None:
            self.children = children  # type: ignore[assignment]
        if parents is not None:
            self.parents = parents  # type: ignore[assignment]
        if presences is not None:
            self.presences = presences  # type: ignore[assignment]
        if names is not None:
            self.names = names  # type: ignore[assignment]

    @property
    def parents(self) -> EntityCollection[Person]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @parents.setter
    def parents(self, parents: Iterable[Person]) -> None:
        pass  # pragma: no cover

    @parents.deleter
    def parents(self) -> None:
        pass  # pragma: no cover

    @property
    def children(self) -> EntityCollection[Person]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @children.setter
    def children(self, children: Iterable[Person]) -> None:
        pass  # pragma: no cover

    @children.deleter
    def children(self) -> None:
        pass  # pragma: no cover

    @property
    def presences(self) -> EntityCollection[Presence]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @presences.setter
    def presences(self, presences: Iterable[Presence]) -> None:
        pass  # pragma: no cover

    @presences.deleter
    def presences(self) -> None:
        pass  # pragma: no cover

    @property
    def names(self) -> EntityCollection[PersonName]:  # type: ignore[empty-body]
        pass  # pragma: no cover

    @names.setter
    def names(self, names: Iterable[PersonName]) -> None:
        pass  # pragma: no cover

    @names.deleter
    def names(self) -> None:
        pass  # pragma: no cover

    @classmethod
    def entity_type_label(cls) -> Str:
        return Str._("Person")  # pragma: no cover

    @classmethod
    def entity_type_label_plural(cls) -> Str:
        return Str._("People")  # pragma: no cover

    @property
    def ancestors(self) -> Iterator[Person]:
        for parent in self.parents:
            yield parent
            yield from parent.ancestors

    @property
    def siblings(self) -> list[Person]:
        siblings = []
        for parent in self.parents:
            for sibling in parent.children:
                if sibling != self and sibling not in siblings:
                    siblings.append(sibling)
        return siblings

    @property
    def descendants(self) -> Iterator[Person]:
        for child in self.children:
            yield child
            yield from child.descendants

    @property
    def associated_files(self) -> Iterable[File]:
        files = [
            *self.files,
            *[
                file
                for name in self.names
                for citation in name.citations
                for file in citation.associated_files
            ],
            *[
                file
                for presence in self.presences
                if presence.event is not None
                for file in presence.event.associated_files
            ],
        ]
        # Preserve the original order.
        seen = set()
        for file in files:
            if file in seen:
                continue
            seen.add(file)
            yield file

    @property
    def label(self) -> Str:
        for name in self.names:
            if name.public:
                return name.label
        return super().label

    async def dump_linked_data(self, app: App) -> DictDump[Dump]:
        dump = await super().dump_linked_data(app)
        dump_context(
            dump,
            names="name",
            parents="parent",
            children="child",
            siblings="sibling",
        )
        dump["@type"] = "https://schema.org/Person"
        dump["parents"] = [
            app.static_url_generator.generate(f"/person/{quote(parent.id)}/index.json")
            for parent in self.parents
            if not isinstance(parent.id, GeneratedEntityId)
        ]
        dump["children"] = [
            app.static_url_generator.generate(f"/person/{quote(child.id)}/index.json")
            for child in self.children
            if not isinstance(child.id, GeneratedEntityId)
        ]
        dump["siblings"] = [
            app.static_url_generator.generate(f"/person/{quote(sibling.id)}/index.json")
            for sibling in self.siblings
            if not isinstance(sibling.id, GeneratedEntityId)
        ]
        dump["presences"] = [
            self._dump_person_presence(presence, app)
            for presence in self.presences
            if presence.event is not None
            and not isinstance(presence.event.id, GeneratedEntityId)
        ]
        if self.public:
            dump["names"] = [
                await name.dump_linked_data(app) for name in self.names if name.public
            ]
        else:
            dump["names"] = []
        return dump

    def _dump_person_presence(self, presence: Presence, app: App) -> DictDump[Dump]:
        assert presence.event
        dump: DictDump[Dump] = {
            "event": app.static_url_generator.generate(
                f"/event/{quote(presence.event.id)}/index.json"
            ),
        }
        dump_context(dump, event="performerIn")
        if presence.public:
            dump["role"] = presence.role.name()
        return dump

    @classmethod
    async def linked_data_schema(cls, app: App) -> DictDump[Dump]:
        schema = await super().linked_data_schema(app)
        add_property(
            schema,
            "names",
            {
                "type": "array",
                "items": await PersonName.linked_data_schema(app),
            },
        )
        add_property(
            schema,
            "parents",
            {
                "$ref": "#/definitions/entity/personCollection",
            },
        )
        add_property(
            schema,
            "children",
            {
                "$ref": "#/definitions/entity/personCollection",
            },
        )
        add_property(
            schema,
            "siblings",
            {
                "$ref": "#/definitions/entity/personCollection",
            },
        )
        presence_schema: DictDump[Dump] = {
            "type": "object",
            "additionalProperties": False,
        }
        add_property(presence_schema, "role", ref_role(schema), False)
        add_property(
            presence_schema,
            "event",
            {
                "type": "string",
                "format": "uri",
            },
        )
        add_json_ld(presence_schema, schema)
        add_property(
            schema,
            "presences",
            {
                "type": "array",
                "items": presence_schema,
            },
        )
        return schema


class Ancestry(MultipleTypesEntityCollection[Entity]):
    def __init__(self):
        super().__init__()
        self._check_graph = True

    def add_unchecked_graph(self, *entities: Entity) -> None:
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
            for association in EntityTypeAssociationRegistry.get_all_associations(
                entity
            ):
                for associate in EntityTypeAssociationRegistry.get_associates(
                    entity, association
                ):
                    yield associate
