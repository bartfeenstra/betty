from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Self, overload

from betty.data import Data
from betty.factory import Manufacturable
from betty.service_level.factory import Integratable

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.service_level import ServiceLevel


class _Configurable[ConfigT: Data]:
    """
    A configurable plugin.

    This internal base class exists only to ensure that multiple manufacturable base classes can be subclasses, but
    only for the same configuration type.
    """


class ConfigurableManufacturable[ConfigT: Data](
    _Configurable[ConfigT], metaclass=ABCMeta
):
    """
    A plugin that can be initialized asynchronously from configuration data.
    """

    @classmethod
    @abstractmethod
    async def new(cls, config: ConfigT, /) -> Self:
        """
        Create a new instance.
        """


class ConfigurableIntegratable[ConfigT: Data](
    _Configurable[ConfigT], metaclass=ABCMeta
):
    """
    A plugin that can be initialized asynchronously for a service level from configuration data.
    """

    @classmethod
    @abstractmethod
    async def new(cls, services: ServiceLevel, config: ConfigT, /) -> Self:
        """
        Create a new instance.
        """


type ManufacturablePlugin[PluginT] = (
    Intersection[PluginT, Manufacturable] | Intersection[PluginT, Callable[[], PluginT]]
)


type IntegrablePlugin[PluginT] = (
    Intersection[PluginT, Integratable] | ManufacturablePlugin[PluginT]
)

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

type ConfigurablePlugin[PluginT, ConfigT: Data] = Intersection[
    PluginT,
    ConfigurableIntegratable[ConfigT] | ConfigurableManufacturable[ConfigT],
]


type PluginFactory[PluginT, NewPluginT: NewPlugin] = (
    type[IntegrablePlugin[PluginT] | ManufacturablePlugin[PluginT]] | NewPluginT
)


type ConfigurablePluginFactory[
    PluginT,
    NewPluginT: NewPlugin,
    ConfigT: Data,
] = type[ConfigurablePlugin[PluginT, ConfigT]] | NewPluginT


type AnyPluginFactory[PluginT, NewPluginT: NewPlugin] = (
    ConfigurablePluginFactory[PluginT, NewPluginT, Data]
    | PluginFactory[PluginT, NewPluginT]
)


@overload
async def new[PluginT, NewPluginT: NewPlugin](
    plugin: PluginFactory[PluginT, NewPluginT],
    services: ServiceLevel,
    /,
) -> PluginT:
    pass


@overload
async def new[PluginT, NewPluginT: NewPlugin, ConfigT: Data](
    plugin: ConfigurablePluginFactory[PluginT, NewPluginT, ConfigT],
    services: ServiceLevel,
    config: ConfigT,
    /,
) -> PluginT:
    pass


async def new(factory, services, config=None, /):
    """
    Initialize a plugin.
    """
    if config is None:
        if issubclass(factory, Integratable):
            return await factory.new(services)
        if issubclass(factory, Manufacturable):
            return await factory.new()
        return await factory()
    if issubclass(factory, ConfigurableIntegratable):
        return await factory.new(services, config)
    return await factory.new(config)
