"""
The service provider API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.classtools import TypeABCMeta
from betty.definition.human_facing import HumanFacingDefinition
from betty.life_cycle.manage import ManagedLifeCycle
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import (
    ManufacturablePlugin,
    NewPlugin,
    Plugin,
    ResolvablePluginManufacturer,
)
from betty.plugin.config import ConfigurablePluginDefinition
from betty.plugin.factory import NewPluginDefinition
from betty.prop import HasProps
from betty.service_level import HasServiceLevel, ServiceLevel

if TYPE_CHECKING:
    from betty.data import Data
    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class ServiceProvider[ServiceLevelT: ServiceLevel = ServiceLevel](
    HasServiceLevel[ServiceLevelT],
    Plugin["ServiceProviderDefinition"],
    HasProps,
    ManagedLifeCycle,
    metaclass=TypeABCMeta,
):
    """
    Integrate custom services with a :py:class:`service level <betty.service_level.ServiceLevel>`.
    """


@final
@PluginTypeDefinition(
    "service-provider",
    label=_("Service provider"),
    label_plural=_("Service providers"),
    label_countable=ngettext("{count} service provider", "{count} service providers"),
)
class ServiceProviderDefinition(
    HumanFacingDefinition, ConfigurablePluginDefinition[ServiceProvider]
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
        config_cls: type[Data] | None = None,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            auto=auto,
            config_cls=config_cls,
            description=description,
            label=label,
            requires=requires,
        )


@final
@NewPluginDefinition(ServiceProviderDefinition)
class NewServiceProvider(NewPlugin[ServiceProviderDefinition, ServiceProvider]):
    """
    The service provider factory.
    """


type ResolvableServiceProviderManufacturer = ResolvablePluginManufacturer[
    ServiceProviderDefinition, NewServiceProvider
]


type ManufacturableServiceProvider[ServiceLevelT: ServiceLevel] = ManufacturablePlugin[
    ServiceProviderDefinition,
    NewServiceProvider,
    ServiceProvider[ServiceLevelT],
]
