"""
Plugin service requirements.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

from betty.locale.localizable.gettext import _
from betty.plugin import PluginDefinition
from betty.plugin.resolve import ResolvablePluginDefinition, resolve_plugin_definition
from betty.requirements.service import UnmetServiceRequirement
from betty.service_level import DownstreamServiceLevel, ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Collection

    from betty.service.plugin import PluginServiceManager, PluginServiceProvider


@final
class PluginServiceRequirement[PluginDefinitionT: PluginDefinition, GetServiceT]:
    """
    A requirement on a plugin service.
    """

    @final
    def __init__(
        self,
        service: PluginServiceManager[
            PluginServiceProvider, PluginDefinitionT, GetServiceT, Any
        ],
        /,
        *plugins: ResolvablePluginDefinition[PluginDefinitionT],
    ):
        self._service = service
        self._plugins = tuple(map(resolve_plugin_definition, plugins))

    @property
    def service(
        self,
    ) -> PluginServiceManager[
        PluginServiceProvider, PluginDefinitionT, GetServiceT, Any
    ]:
        """
        The service for which the plugin is required.
        """
        return self._service

    @property
    def plugins(self) -> Collection[PluginDefinitionT]:
        """
        The definitions of the required service plugins.
        """
        return self._plugins

    async def __call__(self, services: ServiceLevel, /) -> GetServiceT:
        """
        Check the requirement.
        """
        if isinstance(services, self.service.prop.owner):
            service_plugins = list(
                map(
                    self._service.resolve_init_plugin_id,
                    self._service.get_plugins(services),
                )
            )
            for plugin in self._plugins:
                if plugin.id not in service_plugins:
                    raise UnmetServiceRequirement(
                        self._service,
                        _(
                            "The {plugin} {plugin_type} plugin is required from the {service} service."
                        ).format(
                            plugin=plugin.id,
                            plugin_type=self._service.plugin_type.type().label,
                            service=self.service.prop.id,
                        ),
                    )
            return self._service.get(services)
        if isinstance(services, DownstreamServiceLevel):
            return await self(services.upstream)
        raise UnmetServiceRequirement(
            self.service,
            _(
                "Cannot locate the {service} service on any available service level."
            ).format(service=self.service.prop.id),
        )
