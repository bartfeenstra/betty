"""
The Link API allows data to reference external resources.
"""

from __future__ import annotations

from typing import final, Any, MutableSequence, TYPE_CHECKING

from typing_extensions import override

from betty.ancestry.description import HasDescription
from betty.ancestry.locale import HasLocale
from betty.ancestry.media_type import HasMediaType
from betty.ancestry.privacy import is_public
from betty.json.linked_data import LinkedDataDumpable, JsonLdObject, dump_link
from betty.json.schema import Object, String, Array
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import (
    OptionalStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
    StaticTranslationsLocalizableSchema,
)
from betty.media_type.media_types import JSON_LD, HTML
from betty.model import Entity, GeneratedEntityId

if TYPE_CHECKING:
    from betty.project import Project
    from betty.serde.dump import DumpMapping, Dump
    from betty.media_type import MediaType


@final
class Link(HasMediaType, HasLocale, HasDescription, LinkedDataDumpable[Object]):
    """
    An external link.
    """

    #: The link's absolute URL
    url: str
    #: The link's `IANA link relationship <https://www.iana.org/assignments/link-relations/link-relations.xhtml>`_.
    relationship: str | None
    #: The link's human-readable label.
    label = OptionalStaticTranslationsLocalizableAttr("label")

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
        self.url = url
        if label:
            self.label = label
        self.relationship = relationship

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["url"] = self.url
        if self.label:
            dump["label"] = await self.label.dump_linked_data(project)
        if self.relationship is not None:
            dump["relationship"] = self.relationship
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> LinkSchema:
        return LinkSchema()


class LinkSchema(JsonLdObject):
    """
    A JSON Schema for :py:class:`betty.ancestry.Link`.
    """

    def __init__(self):
        super().__init__(def_name="link", title="Link")
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


class LinkCollectionSchema(Array):
    """
    A JSON Schema for :py:class:`betty.ancestry.Link` collections.
    """

    def __init__(self):
        super().__init__(LinkSchema(), def_name="linkCollection", title="Links")


class HasLinks(Entity):
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

        if not isinstance(self.id, GeneratedEntityId):
            await dump_link(
                dump,
                project,
                Link(
                    project.static_url_generator.generate(
                        f"/{self.type.plugin_id()}/{self.id}/index.json"
                    ),
                    relationship="canonical",
                    media_type=JSON_LD,
                ),
            )
            if is_public(self):
                await dump_link(
                    dump,
                    project,
                    *(
                        Link(
                            project.url_generator.generate(
                                self,
                                media_type="text/html",
                                locale=locale,
                            ),
                            relationship="alternate",
                            media_type=HTML,
                            locale=locale,
                        )
                        for locale in project.configuration.locales
                    ),
                )

        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        schema = await super().linked_data_schema(project)
        schema.add_property("links", LinkCollectionSchema())
        return schema
