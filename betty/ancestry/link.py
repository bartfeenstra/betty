"""
The Link API allows data to reference external resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, final

from typing_extensions import override

from betty.ancestry.description import HasDescription
from betty.ancestry.locale import HasLocale
from betty.ancestry.media_type import HasMediaType
from betty.json.linked_data import (
    JsonLdObject,
    JsonLdSchema,
    LinkedDataDumpableJsonLdObject,
    dump_link,
)
from betty.json.schema import Array, String
from betty.link import Link as StdLink
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import (
    OptionalStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    StaticTranslationsLocalizable,
    StaticTranslationsLocalizableSchema,
)
from betty.privacy import is_public

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from betty.media_type import MediaType
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
class Link(
    StdLink, HasMediaType, HasLocale, HasDescription, LinkedDataDumpableJsonLdObject
):
    """
    An external link.
    """

    #: The link's `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.
    relationship: str | None
    _label = OptionalStaticTranslationsLocalizableAttr("_label", title="Label")

    def __init__(
        self,
        url: str,
        *,
        relationship: str | None = None,
        label: ShorthandStaticTranslations | None = None,
        description: ShorthandStaticTranslations | None = None,
        media_type: MediaType | None = None,
        locale: str = UNDETERMINED_LOCALE,
    ):
        super().__init__(
            media_type=media_type,
            description=description,
            locale=locale,
        )
        self._url = url
        if label:
            self._label = label
        self.relationship = relationship

    @override
    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, url: str) -> None:
        self._url = url

    @override
    @property
    def label(self) -> StaticTranslationsLocalizable:
        return self._label

    @label.setter
    def label(self, label: ShorthandStaticTranslations) -> None:
        self._label = label

    @label.deleter
    def label(self) -> None:
        del self._label

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["url"] = self.url
        if self._label:
            dump["label"] = await self._label.dump_linked_data(project)
        if self.relationship is not None:
            dump["relationship"] = self.relationship
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> LinkSchema:
        return await LinkSchema.new()


@final
class LinkSchema(JsonLdObject):
    """
    A JSON Schema for :py:class:`betty.ancestry.link.Link`.
    """

    def __init__(self, json_ld_schema: JsonLdSchema):
        super().__init__(json_ld_schema, def_name="link", title="Link")
        self.add_property(
            "url",
            String(
                format=String.Format.URI,
                description="The full URL to the other resource.",
            ),
        )
        self.add_property(
            "relationship",
            String(
                description="The relationship between this resource and the link target (https://en.wikipedia.org/wiki/Link_relation)."
            ),
            False,
        )
        self.add_property(
            "label",
            StaticTranslationsLocalizableSchema(
                title="Label", description="The human-readable link label."
            ),
            False,
        )

    @classmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """
        return cls(await JsonLdSchema.new())


class LinkCollectionSchema(Array):
    """
    A JSON Schema for :py:class:`betty.ancestry.link.Link` collections.
    """

    def __init__(self, link_schema: LinkSchema):
        super().__init__(link_schema, def_name="linkCollection", title="Links")

    @classmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """
        return cls(await LinkSchema.new())


class HasLinks(LinkedDataDumpableJsonLdObject):
    """
    A resource that has external links.
    """

    def __init__(
        self,
        *args: Any,
        links: MutableSequence[Link] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._links: MutableSequence[Link] = links if links else []

    @property
    def links(self) -> MutableSequence[Link]:
        """
        The extenal links.
        """
        return self._links

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        await dump_link(
            dump,
            project,
            *(self.links if is_public(self) else ()),
        )

        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("links", await LinkCollectionSchema.new())
        return schema
