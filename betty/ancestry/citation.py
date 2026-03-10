"""
Data types for citations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.ancestry.date import HasDate
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_links import HasLinks
from betty.ancestry.source import Source
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.property import LocalizableProperty
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.model import EntityDefinition
from betty.model.association import (
    BidirectionalToManyMultipleTypes,
    BidirectionalToOne,
    ToManyAssociates,
    ToOneAssociate,
)
from betty.privacy import HasPrivacy, Privacy, is_public, merge_secondary_privacies
from betty.property import Optional

if TYPE_CHECKING:
    from betty.ancestry.file_reference import FileReference
    from betty.ancestry.has_citations import HasCitations
    from betty.date import ResolvableDate
    from betty.json.linked_data import JsonLdObject
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "citation",
    label=_("Citation"),
    label_plural=_("Citations"),
    label_countable=ngettext("{count} citation", "{count} citations"),
)
class Citation(HasDate, HasFileReferences, HasPrivacy, HasLinks):
    """
    .. plugin:: entity:citation.
    """

    location = Optional(LocalizableProperty(label=_("Location")))
    """
    The location within the source this citation references.
    """

    facts = BidirectionalToManyMultipleTypes["Citation", "HasCitations"](
        "betty.ancestry.has_citations:HasCitations",
        "citations",
        label=_("Facts"),
        description=_(
            "The other entities that reference these citations to back up their claims."
        ),
    )
    """
    The other entities that reference these citations to back up their claims.
    """

    source = BidirectionalToOne["Citation", Source](
        "betty.ancestry.source:Source",
        "citations",
        label=_("Source"),
        description=_("The source this citation references."),
    )
    """
    The source this citation references.
    """

    def __init__(
        self,
        *,
        source: ToOneAssociate[Source],
        id: str | None = None,  # noqa: A002
        facts: ToManyAssociates[HasCitations] | None = None,
        location: ResolvableLocalizable | None = None,
        date: ResolvableDate | None = None,
        file_references: ToManyAssociates[FileReference] | None = None,
        privacy: Privacy | None = None,
    ):
        super().__init__(
            id,
            date=date,
            file_references=file_references,
            privacy=privacy,
        )
        if facts is not None:
            self.facts = facts
        self.location = location
        self.source = source

    @override
    def _get_effective_privacy(self) -> Privacy:
        return merge_secondary_privacies(super()._get_effective_privacy(), self.source)

    @override
    @property
    def label(self) -> Localizable:
        return self.location or super().label

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        linked_data = dict(await super().dump_linked_data(project))
        linked_data["@type"] = "https://schema.org/Thing"
        if is_public(self) and self.location is not None:
            linked_data["location"] = dump_linked_data(
                self.location, localizers=await project.public_localizers
            )
        return linked_data

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "location",
            StaticTranslationsSchema(),
            False,
        )
        return schema
