"""
The Link API allows data to reference external resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.associations.has_links import HasLinks
from betty.associations.to_one import ToOne
from betty.attrs.description import HasDescription
from betty.attrs.localizable import new_localizable_attr
from betty.attrs.media_type import HasMediaType
from betty.attrs.owner import OwnerAttr
from betty.attrs.privacy import HasPrivacy
from betty.datas.str import StrDefinition
from betty.entity import Entity, EntityDefinition
from betty.link import Link as LinkType
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy
from betty.privacy.resolve import merge_privacies

if TYPE_CHECKING:
    from betty.association import Associate
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.media_type import ResolvableMediaType


@final
@EntityDefinition(
    "link",
    label=_("Link"),
    label_plural=_("Links"),
    label_countable=ngettext("{count} link", "{count} links"),
    public_facing=False,
)
class Link(LinkType, HasMediaType, HasDescription, Entity):
    """
    .. plugin:: entity:link.
    """

    url = new_localizable_attr(label=_("URL"))
    _label = new_localizable_attr(label=_("Label")).optional

    relationship = OwnerAttr(StrDefinition(label=_("Relationship"))).optional
    """
    The link's `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.
    """

    owner = ToOne(HasLinks, "links", label=_("Owner")).optional
    """
    The entity that owns the link.
    """

    def __init__(
        self,
        url: ResolvableLocalizable,
        *,
        id: ResolvableMachineName | None = None,  # noqa: A002
        relationship: str | None = None,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        media_type: ResolvableMediaType | None = None,
        owner: Associate[HasLinks] | None = None,
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(
            id=id, media_type=media_type, description=description, privacy=privacy
        )
        self.url = url
        self._label = label
        self.relationship = relationship
        if owner is not None:
            self.owner = owner

    @override
    @property
    def label(self) -> Localizable:
        return self.url if self._label is None else self._label

    @label.setter
    def label(self, label: ResolvableLocalizable | None) -> None:
        self._label = label

    @label.deleter
    def label(self) -> None:
        del self._label

    @property
    def has_label(self) -> bool:
        """
        Whether the link has an explicit label set.
        """
        return self._label is not None

    @override
    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if isinstance(self.owner, HasPrivacy):
            return merge_privacies(privacy, self.owner)
        return privacy
