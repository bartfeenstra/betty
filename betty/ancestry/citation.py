from __future__ import annotations

from typing import final, Iterable, Any
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry import HasDate, HasFileReferences, HasPrivacy, HasLinks, Source, FileReference, \
    Privacy, merge_privacies
from betty.date import Datey
from betty.json.schema import Object, Array, String
from betty.locale.localizable import _, OptionalStaticTranslationsLocalizableAttr, ShorthandStaticTranslations, \
    Localizable
from betty.model import UserFacingEntity, Entity, GeneratedEntityId, EntityReferenceSchema, \
    EntityReferenceCollectionSchema
from betty.model.association import ManyToMany, ManyToOne
from betty.plugin import ShorthandPluginBase
from betty.project import Project
from betty.serde.dump import DumpMapping, Dump


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
