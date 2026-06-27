"""
The Link API allows data to reference external resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.associations.has_links import HasLinks
from betty.associations.to_one import ToOne
from betty.attrs.description import HasDescription
from betty.attrs.localizable import new_localizable_attr
from betty.attrs.media_type import HasMediaType
from betty.attrs.owner import OwnerAttr
from betty.datas.str import StrDefinition
from betty.entity import Entity, EntityDefinition
from betty.json_schema import String
from betty.json_schemas.static_translations import StaticTranslationsSchema
from betty.link import Link as LinkType
from betty.localizable.linked_data import dump_linked_data
from betty.localizables.gettext import _, ngettext
from betty.privacy import Privacy

if TYPE_CHECKING:
    from betty.association import Associate
    from betty.linked_data import JsonLdObject
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
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

    owner = ToOne[Self, HasLinks](HasLinks, "links", label=_("Owner")).optional
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
        owner: Associate[Self, HasLinks] | None = None,
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
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        public_localizers = await project.public_localizers
        portable = await super().dump_linked_data(project)
        if self.privacy.publishable:
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
