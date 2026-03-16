"""
The Link API allows data to reference external resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.ancestry.description import HasDescription
from betty.ancestry.media_type import HasMediaType
from betty.json.schema import String
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.property import LocalizableProperty
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.model import Entity, EntityDefinition
from betty.model.association import BidirectionalToZeroOrOne
from betty.privacy import HasPrivacy, Privacy, merge_privacies
from betty.property import Optional

if TYPE_CHECKING:
    from betty.ancestry.has_links import HasLinks
    from betty.json.linked_data import JsonLdObject
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.media_type import MediaType
    from betty.portable import PortableMapping
    from betty.project import Project


@final
@EntityDefinition(
    "link",
    label=_("Link"),
    label_plural=_("Links"),
    label_countable=ngettext("{count} link", "{count} links"),
    public_facing=False,
)
class Link(HasMediaType, HasDescription, HasPrivacy, Entity):
    """
    .. plugin:: entity:link.
    """

    _url = LocalizableProperty(label=_("URL"))
    _label = Optional(LocalizableProperty(label=_("Label")))

    relationship: str | None
    """
    The link's `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.
    """

    owner = BidirectionalToZeroOrOne["Link", "HasLinks"](
        "betty.ancestry.has_links:HasLinks",
        "links",
        label=_("Owner"),
    )
    """
    The entity hat owns the link.
    """

    def __init__(
        self,
        url: ResolvableLocalizable,
        *,
        relationship: str | None = None,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        media_type: MediaType | None = None,
        owner: HasLinks | None = None,
        privacy: Privacy | None = None,
    ):
        super().__init__(
            media_type=media_type, description=description, privacy=privacy
        )
        self._url = url
        self._label = label
        self.relationship = relationship
        if owner is not None:
            self.owner = owner

    @property
    def url(self) -> Localizable:
        """
        The URL the link points to.
        """
        return self._url

    @url.setter
    def url(self, url: ResolvableLocalizable) -> None:
        self._url = url

    @override
    @property
    def label(self) -> Localizable:
        """
        The human-readable short link label.
        """
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
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        public_localizers = await project.public_localizers
        portable = await super().dump_linked_data(project)
        if self.public:
            portable["url"] = dump_linked_data(self.url, localizers=public_localizers)
            if self._label is not None:
                portable["label"] = dump_linked_data(
                    self._label, localizers=public_localizers
                )
            if self.relationship is not None:
                portable["relationship"] = self.relationship
        return portable

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "url",
            StaticTranslationsSchema(
                title="Label", description="The full URL to the other resource."
            ),
            False,
        )
        schema.add_property(
            "relationship",
            String(
                description="The relationship between this resource and the link target (https://en.wikipedia.org/wiki/Link_relation)."
            ),
            False,
        )
        schema.add_property(
            "label",
            StaticTranslationsSchema(
                title="Label", description="The human-readable link label."
            ),
            False,
        )
        return schema

    @override
    def _get_effective_privacy(self) -> Privacy:
        privacy = super()._get_effective_privacy()
        if isinstance(self.owner, HasPrivacy):
            return merge_privacies(privacy, self.owner)
        return privacy
