"""
The Link API allows data to reference external resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.description import HasDescription
from betty.ancestry.media_type import HasMediaType
from betty.json.schema import String
from betty.locale.localizable.attr import (
    OptionalLocalizableAttr,
    RequiredLocalizableAttr,
)
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.model import Entity, EntityDefinition
from betty.model.association import BidirectionalToZeroOrOne
from betty.privacy import HasPrivacy, Privacy, merge_privacies

if TYPE_CHECKING:
    from betty.ancestry.has_links import HasLinks
    from betty.json.linked_data import JsonLdObject
    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.media_type import MediaType
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


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
    An external link.
    """

    _url = RequiredLocalizableAttr("_url")
    _label = OptionalLocalizableAttr("_label")

    relationship: str | None
    """
    The link's `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.
    """

    owner = BidirectionalToZeroOrOne["Link", "HasLinks"](
        "betty.ancestry.link:Link",
        "owner",
        "betty.ancestry.has_links:HasLinks",
        "links",
        title="Owner",
    )
    """
    The entity hat owns the link.
    """

    def __init__(
        self,
        url: LocalizableLike,
        *,
        relationship: str | None = None,
        label: LocalizableLike | None = None,
        description: LocalizableLike | None = None,
        media_type: MediaType | None = None,
        owner: HasLinks | None = None,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
    ):
        super().__init__(
            media_type=media_type,
            description=description,
            privacy=privacy,
            public=public,
            private=private,
        )
        self._url = url
        self._label = label
        self.relationship = relationship
        if owner is not None:
            self.owner = owner

    @override
    @property
    def url(self) -> Localizable:
        return self._url

    @url.setter
    def url(self, url: LocalizableLike) -> None:
        self._url = url

    @override  # type: ignore[explicit-override]
    @property
    def label(self) -> Localizable:
        """
        The human-readable short link label.
        """
        return self.url if self._label is None else self._label

    @label.setter
    def label(self, label: LocalizableLike | None) -> None:
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
    async def dump_linked_data(self, project: Project, /) -> DumpMapping[Dump]:
        public_localizers = await project.public_localizers
        dump = await super().dump_linked_data(project)
        if self.public:
            dump["url"] = dump_linked_data(self.url, localizers=public_localizers)
            if self._label is not None:
                dump["label"] = dump_linked_data(
                    self._label, localizers=public_localizers
                )
            if self.relationship is not None:
                dump["relationship"] = self.relationship
        return dump

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
        if isinstance(self.owner, HasPrivacy):  # type: ignore[redundant-expr]
            return merge_privacies(privacy, self.owner)  # type: ignore[unreachable]
        return privacy
