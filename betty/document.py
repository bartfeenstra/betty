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
    Self,
    final,
    override,
)

from betty.json.linked_data import LinkedDataDumpable
from betty.locale.localizable.gettext import _, ngettext
from betty.locale.localize import DEFAULT_LOCALIZER, Localizer
from betty.media_type.media_types import HTML
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.portable import PortableMapping
from betty.service.plugin import ServicePluginDefinition

if TYPE_CHECKING:
    from betty.entity import Entity
    from betty.job import Context
    from betty.locale.localizable import Localizable
    from betty.machine_name import MachineName
    from betty.plugins.entity.citation import Citation
    from betty.project import Project

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
        *,
        breadcrumbs: Breadcrumbs | None = None,
        citer: Citer | None = None,
        entity_contexts: EntityContexts | None = None,
        context: Context | None = None,
        localizer: Localizer | None = None,
        title: Localizable | None = None,
        **vars: Any,  # noqa: A002
    ):
        self._resource = resource
        self._resource_url = resource_url
        self._entity_contexts = entity_contexts if entity_contexts else EntityContexts()
        self._context = context
        self._localizer = localizer if localizer else DEFAULT_LOCALIZER
        self._title = title
        self._vars = vars
        self._breadcrumbs = Breadcrumbs() if breadcrumbs is None else breadcrumbs
        self._citer = Citer() if citer is None else citer

    @property
    def breadcrumbs(self) -> Breadcrumbs:
        """
        The breadcrumbs.
        """
        return self._breadcrumbs

    @property
    def citer(self) -> Citer:
        """
        The citer.
        """
        return self._citer

    @property
    def entity_contexts(self) -> EntityContexts:
        """
        The entity contexts.
        """
        return self._entity_contexts

    @property
    def context(self) -> Context | None:
        """
        The job context.
        """
        return self._context

    @property
    def localizer(self) -> Localizer:
        """
        The localizer.
        """
        return self._localizer

    @property
    def resource(self) -> object:
        """
        The resource itself.
        """
        return self._resource

    @property
    def resource_url(self) -> object:
        """
        The URL-generatable version of the resource itself.

        This may be the resource itself or a completely different type of value.
        """
        return self._resource_url

    @property
    def title(self) -> Localizable | None:
        """
        The human-readable title.
        """
        return self._title

    def copy(
        self,
        **vars: object,  # noqa: A002
    ) -> Self:
        """
        Create a copy of this document, with the given fields added.
        """
        return type(self)(
            **{
                **self._vars,
                "resource": self._resource,
                "resource_url": self._resource_url,
                "breadcrumbs": self._breadcrumbs,
                "citer": self._citer,
                "entity_contexts": self._entity_contexts,
                "context": self._context,
                "localizer": self._localizer,
                "title": self._title,
                **vars,
            },  # ty:ignore[invalid-argument-type]
        )

    def __getitem__(self, var: str) -> object:
        return self._vars[var]

    def __setitem__(self, var: str, value: object) -> None:
        self._vars[var] = value

    def __contains__(self, var: str) -> bool:
        return var in self._vars

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Document):
            return NotImplemented
        return (
            self._resource == other._resource
            and self._resource_url == other._resource_url
            and self._entity_contexts == other._entity_contexts
            and self._context == other._context
            and self._localizer == other._localizer
            and self._title == other._title
            and self._breadcrumbs == other._breadcrumbs
            and self._citer == other._citer
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
class DocumentProviderDefinition(ServicePluginDefinition[DocumentProvider]):
    """
    .. plugin_type:: document-provider.
    """


@final
class DocumentProviderManufacturer(
    PluginManufacturer[DocumentProviderDefinition, DocumentProvider]
):
    """
    The document provider manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[DocumentProviderDefinition]:
        return DocumentProviderDefinition


@final
class Breadcrumb(LinkedDataDumpable[PortableMapping]):
    """
    A breadcrumb.
    """

    def __init__(self, label: str, resource: object | None, /):
        self._label = label
        self._resource_url = resource

    @property
    def label(self) -> str:
        """
        The localized, human-readable label.
        """
        return self._label

    @property
    def resource_url(self) -> object | None:
        """
        The resource URL.
        """
        return self._resource_url

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable: PortableMapping = {
            "@type": "ListItem",
            "name": self._label,
        }
        if self._resource_url is not None:
            url_generator = await project.url_generator
            portable["item"] = url_generator.generate(
                self._resource_url, absolute=True, media_type=HTML
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


class Citer:
    """
    Track citations when they are first used.
    """

    __slots__ = "_lock", "_cited"

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
