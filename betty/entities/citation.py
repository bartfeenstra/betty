"""
Data types for citations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_citations import HasCitations
from betty.associations.has_file_references import HasFileReferences
from betty.associations.has_links import HasLinks
from betty.associations.to_many import ToMany, ToManyAssociates
from betty.associations.to_one import ToOne, ToOneAssociate
from betty.attrs.date import HasAnyDate
from betty.attrs.localizable import new_localizable_attr
from betty.entities.source import Source
from betty.entity import EntityDefinition
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy
from betty.privacy.resolve import merge_secondary_privacies

if TYPE_CHECKING:
    from betty.date import AnyDate
    from betty.entities.file_reference import FileReference
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName


@final
@EntityDefinition(
    "citation",
    label=_("Citation"),
    label_plural=_("Citations"),
    label_countable=ngettext("{count} citation", "{count} citations"),
)
class Citation(HasAnyDate, HasFileReferences, HasLinks):
    """
    .. plugin:: entity:citation.
    """

    location = new_localizable_attr(label=_("Location")).optional
    """
    The location within the source this citation references.
    """

    facts = ToMany[Self, HasCitations](
        HasCitations,
        "citations",
        label=_("Facts"),
        description=_(
            "The other entities that reference these citations to back up their claims."
        ),
    )
    """
    The other entities that reference these citations to back up their claims.
    """

    source = ToOne[Self, Source](
        Source,
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
        source: ToOneAssociate[Self, Source],
        facts: ToManyAssociates[Self, HasCitations] = (),
        id: ResolvableMachineName | None = None,  # noqa: A002
        location: ResolvableLocalizable | None = None,
        date: AnyDate | None = None,
        files: ToManyAssociates[Self, FileReference] = (),
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(
            id=id,
            date=date,
            files=files,
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
