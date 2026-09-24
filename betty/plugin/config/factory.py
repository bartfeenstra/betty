"""
The configurable plugin factory API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from json import dumps
from typing import TYPE_CHECKING, Self, final, overload, override

from typing_extensions import sentinel

from betty.assertions.if_else import assert_if_else
from betty.assertions.mapping import assert_mapping
from betty.assertions.record import Field, assert_record
from betty.attrs.owner import OwnerAttr
from betty.data import Data, DataDefinition
from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin.cls.factory import PluginFactory, PluginManufacturer
from betty.plugin.cls.factory import new as cls_new
from betty.plugin.config import ConfigurablePluginDefinition, NotConfigurable
from betty.portable import KeyedPorter, PortableData

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.definition import ResolvableDefinition
    from betty.definition.id import ResolvableId
    from betty.service_level import ServiceLevel


# @todo These core types should not be part of the plugin API, but something lower level.
class Configurable[ConfigT: Data](metaclass=ABCMeta):
    """
    A plugin that can be initialized asynchronously for a service level from configuration data.
    """

    @classmethod
    @abstractmethod
    async def new(cls, services: ServiceLevel, config: ConfigT, /) -> Self:
        """
        Create a new instance.
        """


type ConfigurablePlugin[PluginT, ConfigT: Data] = Intersection[
    PluginT,
    ConfigurableIntegratable[ConfigT] | ConfigurableManufacturable[ConfigT],
]


type ConfigurablePluginFactory[
    PluginT,
    NewPluginT: NewConfigurablePlugin,
    ConfigT: Data,
] = type[ConfigurablePlugin[PluginT, ConfigT]] | NewPluginT


@overload
async def new[PluginT, NewPluginT: NewConfigurablePlugin](
    plugin: PluginFactory[PluginT, NewPluginT],
    services: ServiceLevel,
    /,
) -> PluginT:
    pass


@overload
async def new[PluginT, NewPluginT: NewConfigurablePlugin, ConfigT: Data](
    plugin: ConfigurablePluginFactory[PluginT, NewPluginT, ConfigT],
    services: ServiceLevel,
    config: ConfigT,
    /,
) -> PluginT:
    pass


async def new(plugin, services, config=None, /):
    """
    Initialize a plugin.
    """
    if config is None:
        return await cls_new(plugin, services)
    if issubclass(plugin, ConfigurableIntegratable):
        return await plugin.new(services, config)
    return await plugin.new(config)


NoConfig = sentinel("NoConfig")


class NewConfigurablePlugin[DefinitionT: ConfigurablePluginDefinition, PluginT](
    PluginManufacturer[DefinitionT, PluginT]
):
    """
    Configure a single configurable plugin instance.
    """

    config = OwnerAttr(
        DataDefinition[Data | PortableData | NoConfig](label=_("Configuration"))
    )
    """
    The plugin configuration.
    """

    @overload
    def __init__(self, plugin_id: ResolvableId[DefinitionT], /):
        pass

    @overload
    def __init__[ConfigT: Data](
        self,
        plugin_id: ResolvableDefinition[DefinitionT],
        plugin_config: ConfigT,
        /,
    ):
        pass

    @overload
    def __init__[ConfigT: Data](
        self, plugin_id: ResolvableMachineName, plugin_config: PortableData, /
    ):
        pass

    @final
    def __init__(self, plugin_id, plugin_config=NoConfig, /):
        super().__init__(plugin_id)
        self.config = plugin_config

    @final
    @override
    def __hash__(self):
        return hash((
            self.definition.plugin_type,
            self.id,
            NoConfig
            if self.config is NoConfig
            else dumps(_NewConfigurablePluginPorter.dump_config(self.config)),
        ))

    @final
    @override
    async def new(self, services: ServiceLevel, /) -> PluginT:
        definition = await services.plugins[self.definition.plugin_type][self.id]
        args = (definition.cls, services)
        if self.config is not NoConfig:
            if not isinstance(definition, ConfigurablePluginDefinition):
                # @todo Add args and such
                raise NotConfigurable
            if not isinstance(self.config, Data):
                self.config = definition.config_cls.definition.porter.load(self.config)
            args += self.config
        return await new(*args)


@final
class _NewConfigurablePluginPorter[NewPluginT: NewConfigurablePlugin](
    KeyedPorter[NewPluginT]
):
    def __init__(self, cls: type[NewPluginT]):
        self._cls = cls

    _load = assert_if_else(
        Pipeline(MachineName.definition.porter.load)
        | (lambda plugin_id: {"plugin": plugin_id}),
        assert_record(
            Field("id", MachineName.definition.porter.load),
            Field("data", optional=True),
        ),
    )

    @override
    def load(self, data: PortableData, /) -> NewPluginT:
        record = self._load(data)
        return self._cls(record["id"], record.get("config", NoConfig))

    _load_keyed = assert_mapping()

    @override
    def load_keyed(self, key: str, data: PortableData, /) -> NewPluginT:
        return self.load({**self._load_keyed(data), "id": key})

    @classmethod
    def dump_config(cls, config: Data | PortableData) -> PortableData:
        if isinstance(config, Data):
            return config.definition.porter.dump(config)
        return config

    @override
    def dump(self, data: NewPluginT, /) -> PortableData:
        if data.config is NoConfig:
            return data.id
        return {
            "id": data.id,
            "config": self.dump_config(data.config),
        }

    @override
    def dump_keyed(self, data: NewPluginT, /) -> tuple[str, PortableData]:
        return data.id, {} if data.config is NoConfig else {
            "config": self.dump_config(data.config)
        }
