"""
Manage documents.

A document is a singular file, such as an HTML page or a JSON file.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sized,
)
from threading import Lock
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Self,
    final,
    override,
)

from betty.linked_data import LinkedDataDumpable
from betty.localizables.gettext import _, ngettext
from betty.localizer import Localizer, default_localizer
from betty.media_type import MediaType, ResolvableMediaType, resolve_media_type
from betty.media_types.html import HTML
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.portable import PortableMapping

if TYPE_CHECKING:
    from betty.entities.citation import Citation
    from betty.entity import Entity
    from betty.job import Context
    from betty.localizable import Localizable
    from betty.machine_name import MachineName, ResolvableMachineName
    from betty.project import Project
    from betty.requirement import Requires

type DocumentVars = Mapping[str, Any]


@final
class Document:
    """
    A document.
    """

    def __init__(
        self,
        resource: object = None,
        resource_url: object = None,
        /,
        *,
        breadcrumbs: Breadcrumbs | None = None,
        citer: Citer | None = None,
        entity_contexts: EntityContexts | None = None,
        context: Context | None = None,
        localizer: Localizer | None = None,
        media_type: ResolvableMediaType | None = None,
        title: Localizable | None = None,
        **document_vars: Any,
    ):
        self.media_type: Final[MediaType | None] = (
            None if media_type is None else resolve_media_type(media_type)
        )
        """
        The media type.
        """
        self.resource: Final[object] = resource
        """
        The resource itself.
        """
        self.resource_url: Final[object] = resource_url
        """
        The URL-generatable version of the resource itself.

        This may be the resource itself or a completely different type of value.
        """
        self.entity_contexts: Final[EntityContexts] = (
            entity_contexts if entity_contexts else EntityContexts()
        )
        """
        The entity contexts.
        """
        self.context: Final[Context | None] = context
        """
        The job context.
        """
        self.localizer: Final[Localizer] = localizer if localizer else default_localizer
        """
        The localizer.
        """
        self.title: Final[Localizable | None] = title
        """
        The human-readable title.
        """
        self._vars = document_vars
        self.breadcrumbs: Final[Breadcrumbs] = (
            Breadcrumbs() if breadcrumbs is None else breadcrumbs
        )
        """
        The breadcrumbs.
        """
        self.citer: Final[Citer] = Citer() if citer is None else citer
        """
        The citer.
        """

    def copy(
        self,
        *,
        media_type: ResolvableMediaType | None = None,
        resource: object = None,
        resource_url: object = None,
        **document_vars: Any,
    ) -> Self:
        """
        Create a copy of this document, with the given fields added.
        """
        return type(self)(
            self.resource if resource is None else resource,
            self.resource_url if resource_url is None else resource_url,
            **{
                **self._vars,
                "breadcrumbs": self.breadcrumbs,
                "citer": self.citer,
                "context": self.context,
                "entity_contexts": self.entity_contexts,
                "localizer": self.localizer,
                "media_type": self.media_type
                if media_type is None
                else resolve_media_type(media_type),
                "title": self.title,
                **document_vars,
            },  # ty:ignore[invalid-argument-type]
        )

    def __getitem__(self, var: str) -> object:
        return self._vars[var]

    def __setitem__(self, var: str, value: object) -> None:
        self._vars[var] = value

    def __contains__(self, var: str) -> bool:
        return var in self._vars

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Document):
            return NotImplemented
        return (
            self.breadcrumbs == other.breadcrumbs
            and self.citer == other.citer
            and self.context == other.context
            and self.entity_contexts == other.entity_contexts
            and self.localizer == other.localizer
            and self.media_type == other.media_type
            and self.resource == other.resource
            and self.resource_url == other.resource_url
            and self.title == other.title
            and self._vars == other._vars
        )


class DocumentProvider(Plugin["DocumentProviderDefinition"]):
    """
    Provide new documents.
    """

    def new_document_vars(self) -> DocumentVars:
        """
        Create new variables for a new :py:class:`betty.document.Document`.

        Keys are the variable names, and values are variable values.
        """
        return {}


@final
@PluginTypeDefinition(
    "document-provider",
    label=_("Document provider"),
    label_plural=_("Document providers"),
    label_countable=ngettext("{count} document provider", "{count} document providers"),
)
class DocumentProviderDefinition(PluginClsDefinition[DocumentProvider]):
    """
    .. plugin_type:: document-provider.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        auto: bool = False,
        requires: Requires = (),
    ):
        super().__init__(plugin_id, auto=auto, requires=requires)


@final
@PluginManufacturerDefinition(DocumentProviderDefinition)
class DocumentProviderManufacturer(
    PluginManufacturer[DocumentProviderDefinition, DocumentProvider]
):
    """
    The document provider manufacturer.
    """


@final
class Breadcrumb(LinkedDataDumpable[PortableMapping]):
    """
    A breadcrumb.
    """

    def __init__(self, label: str, resource: object | None, /):
        self.label: Final[str] = label
        """
        The localized, human-readable label.
        """
        self.resource_url: Final[object | None] = resource
        """
        The resource URL.
        """

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable: PortableMapping = {
            "@type": "ListItem",
            "name": self.label,
        }
        if self.resource_url is not None:
            url_generator = await project.url_generator
            portable["item"] = url_generator.generate(
                self.resource_url, absolute=True, media_type=HTML
            )
        return portable


@final
class Breadcrumbs(LinkedDataDumpable[PortableMapping], Iterable[Breadcrumb], Sized):
    """
    A trail of navigational breadcrumbs.
    """

    def __init__(self):
        self._breadcrumbs: MutableSequence[Breadcrumb] = []

    @override
    def __iter__(self) -> Iterator[Breadcrumb]:
        return iter(self._breadcrumbs)

    @override
    def __len__(self) -> int:
        return len(self._breadcrumbs)

    def append(self, label: str, resource_url: object | None = None, /) -> None:
        """
        Append a breadcrumb to the trail.
        """
        self._breadcrumbs.append(Breadcrumb(label, resource_url))

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        if not self._breadcrumbs:
            return {}
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "position": position,
                    **await breadcrumb.dump_linked_data(project),
                }
                for position, breadcrumb in enumerate(self._breadcrumbs, 1)
            ],
        }


@final
class Citer:
    """
    Track citations when they are first used.
    """

    __slots__ = "_cited", "_lock"

    def __init__(self):
        self._lock = Lock()
        self._cited: MutableSequence[Citation] = []

    def __iter__(self) -> enumerate[Citation]:
        return enumerate(self._cited, 1)

    def __len__(self) -> int:
        return len(self._cited)

    def cite(self, citation: Citation, /) -> int:
        """
        Reference a citation.

        :returns: The citation's sequential reference number.
        """
        with self._lock:
            if citation not in self._cited:
                self._cited.append(citation)
            return self._cited.index(citation) + 1


@final
class EntityContexts:
    """
    Track the current entity contexts.

    To allow templates to respond to their environment, this class allows
    our templates to set and get one entity per entity type for the current context.

    Use cases include rendering an entity label as plain text if the template is in
    that entity's context, but as a hyperlink if the template is not in the entity's
    context.
    """

    def __init__(self, *entities: Entity) -> None:
        self._contexts: MutableMapping[MachineName, Entity | None] = defaultdict(
            lambda: None
        )
        for entity in entities:
            self._contexts[entity.plugin().id] = entity

    def __getitem__(self, entity_type: ResolvablePluginId) -> Entity | None:
        return self._contexts[resolve_plugin_id(entity_type)]

    def __call__(self, *entities: Entity) -> EntityContexts:
        """
        Create a new context with the given entities.
        """
        updated_contexts = EntityContexts(
            *(entity for entity in self._contexts.values() if entity is not None)
        )
        for entity in entities:
            updated_contexts._contexts[entity.plugin().id] = entity
        return updated_contexts
