"""
The universal service level.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Self, final

from typing_extensions import TypeVar, override

from betty.plugin import PluginDefinition
from betty.plugin.repository.provider.service import (
    ServiceLevelPluginRepositoryProvider,
)
from betty.service.level import ServiceLevel

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.machine_name import MachineName
    from betty.plugin.repository import PluginRepository

_T = TypeVar("_T")
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


@final
class _UniversalServiceLevel(ServiceLevel):
    def __init__(self):
        super().__init__()
        self._plugin_repository_provider = ServiceLevelPluginRepositoryProvider(self)

    @classmethod
    async def requires(
        cls, services: ServiceLevel, subject: ResolvableLocalizable, /
    ) -> Self:
        return universe  # ty:ignore[invalid-return-type]

    @override
    async def plugins(
        self,
        plugin_type: type[_PluginDefinitionT] | MachineName,
        *,
        check_requirements: bool = True,
    ) -> PluginRepository[_PluginDefinitionT]:
        return await self._plugin_repository_provider.plugins(
            plugin_type, check_requirements=check_requirements
        )  # ty:ignore[invalid-return-type]


universe: Final[ServiceLevel] = _UniversalServiceLevel()
"""
The universal service level.
"""
