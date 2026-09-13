"""
The configurable plugin factory API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from json import dumps
from typing import TYPE_CHECKING, Final, Self, final, overload, override

from typing_extensions import sentinel

from betty.assertions.if_else import assert_if_else
from betty.assertions.mapping import assert_mapping
from betty.assertions.record import Field, assert_record
from betty.attrs.owner import OwnerAttr
from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin.cls.factory import PluginFactory, _NewPlugin
from betty.plugin.cls.factory import new as cls_new
from betty.plugin.config import ConfigurablePluginDefinition, NotConfigurable
from betty.portable import KeyedPorter, PortableData

if TYPE_CHECKING:
    from ty_extensions import Intersection

    from betty.plugin.resolve import (
        ResolvablePluginDefinition,
        ResolvablePluginId,
    )
    from betty.service_level import ServiceLevel


class _Configurable[ConfigT: Data]:
    """
    A configurable plugin.

    This internal base class exists only to ensure that multiple manufacturable base classes can be subclassed, but
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


# @todo Move this onto NewPlugin?
# @todo Except that for non-configurable
# @todo
# @todo
# @todo
NoConfig = sentinel("NoConfig")


class NewConfigurablePlugin[PluginDefinitionT: ConfigurablePluginDefinition, PluginT](
    _NewPlugin[PluginDefinitionT, PluginT]
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
    def __init__(self, plugin_id: ResolvablePluginId[PluginDefinitionT], /):
        pass

    @overload
    def __init__[ConfigT: Data](
        self,
        plugin_id: ResolvablePluginDefinition[PluginDefinitionT],
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
            self.data().plugin_type,
            self.id,
            NoConfig
            if self.config is NoConfig
            else dumps(_NewConfigurablePluginPorter.dump_config(self.config)),
        ))

    @final
    @override
    async def new(self, services: ServiceLevel, /) -> PluginT:
        definition = await services.plugins[self.data().plugin_type][self.id]
        args = (definition.cls, services)
        if self.config is not NoConfig:
            if not isinstance(definition, ConfigurablePluginDefinition):
                # @todo Add args and such
                raise NotConfigurable
            if not isinstance(self.config, Data):
                self.config = definition.config_cls.data().porter.load(self.config)
            args += self.config
        return await new(*args)


@final
class _NewConfigurablePluginPorter[NewPluginT: NewConfigurablePlugin](
    KeyedPorter[NewPluginT]
):
    def __init__(self, cls: type[NewPluginT]):
        self._cls = cls

    _load = assert_if_else(
        Pipeline(MachineName.data().porter.load)
        | (lambda plugin_id: {"plugin": plugin_id}),
        assert_record(
            Field("id", MachineName.data().porter.load),
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
            return config.data().porter.dump(config)
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


@final
class NewConfigurablePluginDefinition[
    PluginDefinitionT: ConfigurablePluginDefinition,
    PluginT,
](ObjectDefinition[NewConfigurablePlugin[PluginDefinitionT, PluginT]]):
    """
    Define a configurable plugin factory.
    """

    def __init__(self, plugin_type: type[PluginDefinitionT], /):
        super().__init__(
            label=plugin_type.type().label,
            porter=lambda definition: _NewConfigurablePluginPorter(definition.cls),
        )
        self.plugin_type: Final[type[PluginDefinitionT]] = plugin_type
