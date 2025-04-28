"""
Data types for citations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import HasLinks
from betty.ancestry.source import Source
from betty.locale.localizable import (
    Localizable,
    OptionalStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    _,
    ngettext,
)
from betty.model import UserFacingEntity
from betty.model.association import (
    BidirectionalToMany,
    BidirectionalToOne,
    ToManyAssociates,
    ToOneAssociate,
)
from betty.plugin import ShorthandPluginBase
from betty.privacy import HasPrivacy, Privacy, merge_secondary_privacies

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
        title="Facts",
        description="The other entities that reference these citations to back up their claims.",
    )
    source = BidirectionalToOne["Citation", Source](
        "betty.ancestry.citation:Citation",
        "source",
        "betty.ancestry.source:Source",
        "citations",
        title="Source",
        description="The source this citation references.",
    )

    #: The human-readable citation location.
    location = OptionalStaticTranslationsLocalizableAttr(
        "location", title="This citation's location within its source."
    )

    def __init__(
        self,
        *,
        source: ToOneAssociate[Source],
        id: str | None = None,  # noqa A002  # noqa A002
        facts: ToManyAssociates[HasCitations & Entity] | None = None,
        location: ShorthandStaticTranslations | None = None,
        date: Datey | None = None,
        file_references: ToManyAssociates[FileReference] | None = None,
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
        return merge_secondary_privacies(super()._get_effective_privacy(), self.source)

    @override
    @classmethod
    def plugin_label_plural(cls) -> Localizable:
        return _("Citations")

    @override
    @classmethod
    def plugin_label_count(cls, count: int) -> Localizable:
        return ngettext("{count} citation", "{count} citations", count).format(
            count=str(count)
        )

    @override
    @property
    def label(self) -> Localizable:
        return self.location or super().label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["@type"] = "https://schema.org/Thing"
        return dump
