"""
Plugin service requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, final

from betty.definition import resolve_definition
from betty.localizables.gettext import _
from betty.plugin import PluginDefinition
from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import DownstreamServiceLevel, ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Collection

    from betty.definition import ResolvableDefinition
    from betty.services.plugin import (
        PluginServiceManager,
        ResolvableServiceLevelHasPluginServices,
    )


@final
class PluginServiceRequirement[DefinitionT: PluginDefinition, GetServiceT]:
    """
    A requirement on a plugin service.
    """

    @final
    def __init__(
        self,
        service: PluginServiceManager[
            ResolvableServiceLevelHasPluginServices, DefinitionT, GetServiceT, Any
        ],
        /,
        *plugins: ResolvableDefinition[DefinitionT],
    ):
        self.service: Final[
            PluginServiceManager[
                ResolvableServiceLevelHasPluginServices,
                DefinitionT,
                GetServiceT,
                Any,
            ]
        ] = service
        """
        The service for which the plugin is required.
        """
        self.plugins: Final[Collection[DefinitionT]] = tuple(
            map(resolve_definition, plugins)
        )
        """
        The definitions of the required service plugins.
        """

    async def __call__(self, services: ServiceLevel, /) -> GetServiceT:
        """
        Check the requirement.
        """
        if isinstance(services, self.service.ownership.owner):
            service_plugins = list(
                map(
                    self.service.resolve_init_plugin_id,
                    self.service.get_plugins(services),
                )
            )
            for plugin in self.plugins:
                if plugin.id not in service_plugins:
                    raise UnmetServiceRequirement(
                        self.service,
                        _(
                            "The {plugin} {plugin_type} plugin is required from the {service} service."
                        ).format(
                            plugin=plugin.id,
                            plugin_type=self.service.plugin_type.definition.label,
                            service=self.service.ownership.fully_qualified_name,
                        ),
                    )
            return self.service.get(services)
        if isinstance(services, DownstreamServiceLevel):
            return await self(services.upstream)
        raise UnmetServiceRequirement(
            self.service,
            _(
                "Cannot locate the {service} service on any available service level."
            ).format(service=self.service.ownership.fully_qualified_name),
        )
