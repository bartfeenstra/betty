"""
Plugin discovery.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import gather
from collections.abc import Awaitable, Callable, Collection, Iterable
from contextlib import contextmanager
from typing import TYPE_CHECKING, Generic, TypeAlias, Unpack, final

import typing_extensions
from typing_extensions import TypeVar

from betty.asyncio import resolve_await
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginDefinition, ResolvableDefinition
from betty.service.requirement import ServiceLevelKwargs

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.service.level import ServiceLevel

_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginDiscovery(ABC, Generic[_PluginDefinitionT]):
    """
    A plugin definition discovery.
    """

    @abstractmethod
    async def discover(
        self, *, services: ServiceLevel
    ) -> Iterable[ResolvableDiscovery[_PluginDefinitionT]]:
        """
        Discover the plugin definitions.
        """


ResolvableDiscoveredDefinition: TypeAlias = (
    ResolvableDefinition[_PluginDefinitionT]
    | tuple[MachineName, Callable[[], Awaitable[_PluginDefinitionT]]]
)

ResolvableDiscovery: TypeAlias = (
    PluginDiscovery[_PluginDefinitionT]
    | Callable[
        [Unpack[ServiceLevelKwargs]],
        Awaitable[Iterable["ResolvableDiscovery[_PluginDefinitionT]"]]
        | Iterable["ResolvableDiscovery[_PluginDefinitionT]"],
    ]
    | ResolvableDiscoveredDefinition[_PluginDefinitionT]
)


async def discover(
    *discoveries: ResolvableDiscovery[_PluginDefinitionT], services: ServiceLevel
) -> Iterable[_PluginDefinitionT]:
    """
    Discover plugins definitions.
    """
    return [
        plugin
        for plugins in await gather(
            *[_discover(discovery, services) for discovery in discoveries]
        )
        for plugin in plugins
    ]


async def _discover(
    discovery: ResolvableDiscovery[_PluginDefinitionT], services: ServiceLevel
) -> Iterable[_PluginDefinitionT]:
    from betty.service.requirement import UnmetRequirement

    try:
        if isinstance(discovery, PluginDiscovery):
            return await discover(
                *await discovery.discover(services=services), services=services
            )  # ty:ignore[invalid-return-type]
        if isinstance(discovery, PluginDefinition):
            return [discovery]  # ty:ignore[invalid-return-type]
        if isinstance(discovery, type) and issubclass(discovery, Plugin):
            return [discovery.plugin()]  # ty:ignore[invalid-return-type]
        return await discover(
            *await resolve_await(discovery(services=services)), services=services
        )  # ty:ignore[invalid-return-type]
    except UnmetRequirement:
        return ()


@final
class Discoverer(PluginDiscovery[_PluginDefinitionT]):
    """
    A plugin discoverer.
    """

    def __init__(
        self,
        discovery: Iterable[ResolvableDiscovery[_PluginDefinitionT]] | None = None,
        /,
    ):
        self._defined = [] if discovery is None else list(discovery)
        self._active: Collection[ResolvableDiscovery[_PluginDefinitionT]] = (
            self._defined
        )

    def add(self, *discoveries: ResolvableDiscovery[_PluginDefinitionT]) -> None:
        """
        Add discoveries.
        """
        self._defined.extend(discoveries)

    @contextmanager
    def override(
        self, *discoveries: ResolvableDiscovery[_PluginDefinitionT]
    ) -> Iterator[None]:
        """
        Temporarily override the defined discoveries with the given discoveries.
        """
        self._active = discoveries
        try:
            yield
        finally:
            self._active = self._defined

    @property
    def overridden(self) -> bool:
        """
        Whether the defined discoveries are currently overridden.
        """
        return self._defined != self._active

    @typing_extensions.override
    async def discover(
        self, *, services: ServiceLevel
    ) -> Iterable[ResolvableDiscoveredDefinition[_PluginDefinitionT]]:
        return await discover(*self._active, services=services)  # ty:ignore[invalid-return-type]
