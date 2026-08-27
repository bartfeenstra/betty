"""
The service provider API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.classtools import TypeABCMeta
from betty.definition.human_facing import HumanFacingDefinition
from betty.factory import Arg1Manufacturable
from betty.life_cycle.manage import ManagedLifeCycle
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition
from betty.prop import HasProps
from betty.service_level import HasServiceLevel, ServiceLevel

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class ServiceProvider[ServiceLevelT: ServiceLevel = ServiceLevel](
    HasServiceLevel[ServiceLevelT],
    Plugin["ServiceProviderDefinition"],
    Arg1Manufacturable[ServiceLevelT],
    HasProps,
    ManagedLifeCycle,
    metaclass=TypeABCMeta,
):
    """
    Integrate custom services with a :py:class:`service level <betty.service_level.ServiceLevel>`.
    """

    @override
    @classmethod
    async def new(cls, services: ServiceLevel, /) -> Self:
        return cls(services=services)


@final
@PluginTypeDefinition(
    "service-provider",
    label=_("Service provider"),
    label_plural=_("Service providers"),
    label_countable=ngettext("{count} service provider", "{count} service providers"),
)
class ServiceProviderDefinition(
    HumanFacingDefinition, PluginClsDefinition[ServiceProvider]
):
    """
    .. plugin_type:: service-provider.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        auto: bool = False,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            label=label,
            description=description,
            requires=requires,
        )


@final
@PluginManufacturerDefinition(ServiceProviderDefinition)
class ServiceProviderManufacturer(
    PluginManufacturer[ServiceProviderDefinition, ServiceProvider]
):
    """
    The service provider manufacturer.
    """
