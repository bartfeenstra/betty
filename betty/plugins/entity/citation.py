"""
Data types for citations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entity import EntityDefinition
from betty.entity.association import (
    BidirectionalToManyMultipleTypes,
    BidirectionalToOne,
    ToManyAssociates,
    ToOneAssociate,
)
from betty.entity.has_file_references import HasFileReferences
from betty.entity.has_links import HasLinks
from betty.locale.localizable.gettext import _, ngettext
from betty.plugins.entity.source import Source
from betty.privacy import Privacy
from betty.privacy.resolve import merge_secondary_privacies
from betty.properties.date import HasAnyDate
from betty.properties.localizable import LocalizableProperty
from betty.properties.privacy import HasPrivacy
from betty.property import Optional

if TYPE_CHECKING:
    from betty.date import AnyDate
    from betty.entity.has_citations import HasCitations
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.plugins.entity.file_reference import FileReference


@final
@EntityDefinition(
    "citation",
    label=_("Citation"),
    label_plural=_("Citations"),
    label_countable=ngettext("{count} citation", "{count} citations"),
)
class Citation(HasAnyDate, HasFileReferences, HasPrivacy, HasLinks):
    """
    .. plugin:: entity:citation.
    """

    location = Optional(LocalizableProperty(label=_("Location")))
    """
    The location within the source this citation references.
    """

    facts = BidirectionalToManyMultipleTypes["Citation", "HasCitations"](
        "betty.entity.has_citations:HasCitations",
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
        "betty.plugins.entity.source:Source",
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
        facts: ToManyAssociates[HasCitations] = (),
        location: ResolvableLocalizable | None = None,
        date: AnyDate | None = None,
        file_references: ToManyAssociates[FileReference] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(
            id,
            date=date,
            file_references=file_references,
            privacy=privacy,
        )
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
