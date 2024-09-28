"""
Data types for citations.
"""

from __future__ import annotations

from typing import final, Iterable, TYPE_CHECKING
from urllib.parse import quote

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import HasLinks
from betty.privacy import HasPrivacy, Privacy, merge_privacies
from betty.ancestry.source import Source
from betty.json.schema import Object, Array, String
from betty.locale.localizable import (
    _,
    OptionalStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    Localizable,
)
from betty.model import (
    UserFacingEntity,
    GeneratedEntityId,
    EntityReferenceSchema,
)
from betty.model.association import (
    BidirectionalToMany,
    BidirectionalToOne,
    ToOneResolver,
    ToManyResolver,
)
from betty.plugin import ShorthandPluginBase

if TYPE_CHECKING:
    from betty.ancestry.has_citations import HasCitations  # noqa F401
    from betty.model import Entity  # noqa F401
    from betty.serde.dump import DumpMapping, Dump
    from betty.project import Project
    from betty.date import Datey
    from betty.ancestry.file_reference import FileReference


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

    facts = BidirectionalToMany["Citation", "HasCitations"](
        "betty.ancestry.citation:Citation",
        "facts",
        "betty.ancestry.has_citations:HasCitations",
        "citations",
    )
    source = BidirectionalToOne["Citation", Source](
        "betty.ancestry.citation:Citation",
        "source",
        "betty.ancestry.source:Source",
        "citations",
    )

    #: The human-readable citation location.
    location = OptionalStaticTranslationsLocalizableAttr("location")

    def __init__(
        self,
        *,
        source: Source | ToOneResolver[Source],
        id: str | None = None,  # noqa A002  # noqa A002
        facts: Iterable["HasCitations & Entity"]
        | ToManyResolver["HasCitations"]
        | None = None,
        location: ShorthandStaticTranslations | None = None,
        date: Datey | None = None,
        file_references: Iterable[FileReference]
        | ToManyResolver[FileReference]
        | None = None,
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
        if not isinstance(self.source.id, GeneratedEntityId):
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
