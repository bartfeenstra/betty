"""
Manage  resources.

A resource is a singular file, such as an HTML page or a JSON file.
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
    TypeAlias,
    TypedDict,
    final,
)

from typing_extensions import override

from betty.json.linked_data import LinkedDataDumpable
from betty.locale.localizer import DEFAULT_LOCALIZER, Localizer
from betty.media_type.media_types import HTML
from betty.plugin import PluginIdentifier, resolve_id
from betty.serde.dump import Dump, DumpMapping

if TYPE_CHECKING:
    from betty.ancestry.citation import Citation
    from betty.job import Context as JobContext
    from betty.locale.localizable import Localizable
    from betty.machine_name import MachineName
    from betty.model import Entity
    from betty.project import Project

ContextVars: TypeAlias = Mapping[str, Any]


class Context(TypedDict):
    """
    The context for a single resource.

    The context describes the resource and manages its metadata and additional tools to work with the resource.
    """

    breadcrumbs: Breadcrumbs
    citer: Citer
    entity_contexts: EntityContexts
    job_context: JobContext | None
    localizer: Localizer
    resource: object
    resource_url: object
    title: Localizable | None


def new_context(
    resource: object = None,
    resource_url: object = None,
    *,
    entity_contexts: EntityContexts | None = None,
    job_context: JobContext | None = None,
    localizer: Localizer | None = None,
    **kwargs: Any,
) -> Context:
    """
    Create a new resource context.
    """
    return {
        "breadcrumbs": Breadcrumbs(),
        "citer": Citer(),
        "entity_contexts": entity_contexts if entity_contexts else EntityContexts(),
        "job_context": job_context,
        "localizer": localizer if localizer else DEFAULT_LOCALIZER,
        "resource": resource,
        "resource_url": resource_url,
        "title": None,
        **kwargs,  # type: ignore[typeddict-item]
    }


def copy_context(context: Context, **kwargs: object) -> Context:
    """
    Create a copy of a context, with the given fields added.
    """
    return {
        **context,
        **kwargs,  # type: ignore[typeddict-item]
    }


class ContextProvider:
    """
    Provide resource context.
    """

    def new_resource_context(self) -> ContextVars:
        """
        Create new variables for a new :py:class:`betty.resource.Context`.

        Keys are the variable names, and values are variable values.
        """
        return {}


@final
class Breadcrumb(LinkedDataDumpable[DumpMapping[Dump]]):
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
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump: DumpMapping[Dump] = {
            "@type": "ListItem",
            "name": self._label,
        }
        if self._resource_url is not None:
            url_generator = await project.url_generator
            dump["item"] = url_generator.generate(
                self._resource_url, absolute=True, media_type=HTML
            )
        return dump


@final
class Breadcrumbs(LinkedDataDumpable[DumpMapping[Dump]], Iterable[Breadcrumb], Sized):
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
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
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

    def cite(self, citation: Citation) -> int:
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
            self._contexts[entity.plugin.id] = entity

    def __getitem__(self, entity_type: PluginIdentifier) -> Entity | None:
        return self._contexts[resolve_id(entity_type)]

    def __call__(self, *entities: Entity) -> EntityContexts:
        """
        Create a new context with the given entities.
        """
        updated_contexts = EntityContexts(
            *(entity for entity in self._contexts.values() if entity is not None)
        )
        for entity in entities:
            updated_contexts._contexts[entity.plugin.id] = entity
        return updated_contexts
