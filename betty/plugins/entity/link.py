"""
The Link API allows data to reference external resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.entity import Entity, EntityDefinition
from betty.entity.association import BidirectionalToZeroOrOne
from betty.json_schema import String
from betty.link import Link as LinkType
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.privacy import Privacy
from betty.privacy.resolve import merge_privacies
from betty.properties.description import HasDescription
from betty.properties.localizable import LocalizableProperty
from betty.properties.media_type import HasMediaType
from betty.properties.privacy import HasPrivacy
from betty.property import Optional

if TYPE_CHECKING:
    from betty.entity.has_links import HasLinks
    from betty.linked_data import JsonLdObject
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.media_type import ResolvableMediaType
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
class Link(LinkType, HasMediaType, HasDescription, HasPrivacy, Entity):
    """
    .. plugin:: entity:link.
    """

    url = LocalizableProperty(label=_("URL"))

    relationship: str | None
    """
    The link's `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.
    """

    owner = BidirectionalToZeroOrOne["Link", "HasLinks"](
        "betty.entity.has_links:HasLinks",
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
        media_type: ResolvableMediaType | None = None,
        owner: HasLinks | None = None,
        privacy: Privacy = Privacy.UNDETERMINED,
    ):
        super().__init__(
            media_type=media_type, description=description, privacy=privacy
        )
        self.url = url
        self.label = label
        self.relationship = relationship
        if owner is not None:
            self.owner = owner

    @override
    @Optional(LocalizableProperty(label=_("Label")))
    def label(self, label: Localizable | None, /) -> Localizable:
        return self.url if label is None else label

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
            portable["label"] = dump_linked_data(
                self.label, localizers=public_localizers
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
