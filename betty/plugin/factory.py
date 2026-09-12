from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Callable
from json import dumps
from typing import TYPE_CHECKING, Final, Self, final, overload, override

from ty_extensions import Intersection
from typing_extensions import disjoint_base, sentinel

from betty.assertions.if_else import assert_if_else
from betty.assertions.mapping import assert_mapping
from betty.assertions.record import Field, assert_record
from betty.attrs.machine_name import new_machine_name_attr
from betty.attrs.owner import OwnerAttr
from betty.classtools import TypeABCMeta
from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.factory import Manufacturable
from betty.freezer import Frozen
from betty.functools import Pipeline
from betty.localizables.gettext import _
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin.cls import ClassedPluginDefinition
from betty.plugin.config import ConfigurablePluginDefinition, NotConfigurable
from betty.plugin.resolve import (
    ResolvablePluginDefinition,
    ResolvablePluginId,
    resolve_plugin_id,
)
from betty.portable import KeyedPorter, PortableData
from betty.prop import HasProps
from betty.sample import Samplable, Sample, Samples, Size
from betty.service_level.factory import Integratable

if TYPE_CHECKING:
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


NoNewPluginConfig = sentinel("NoNewPluginConfig")


# @todo Create a non-configurable and a configurable version of this
@disjoint_base
class NewPlugin[PluginDefinitionT: ClassedPluginDefinition, PluginT](
    Samplable,
    Data["NewPluginDefinition[PluginDefinitionT, PluginT]"],
    HasProps,
    Frozen,
    metaclass=TypeABCMeta,
):
    """
    Configure a single plugin instance.
    """

    id = new_machine_name_attr(label=_("ID"))
    """
    The plugin ID.
    """

    config = OwnerAttr(
        DataDefinition[Data | PortableData | NoNewPluginConfig](
            label=_("Configuration")
        )
    )
    """
    Get the plugin's own configuration.
    """

    @overload
    def __init__(self, plugin_id: ResolvablePluginId[PluginDefinitionT], /):
        pass

    @overload
    def __init__[ConfigT: Data](
        self,
        plugin_id: ResolvablePluginDefinition[
            Intersection[
                PluginDefinitionT,
                ConfigurablePluginDefinition[
                    ConfigurablePlugin[PluginT, ConfigT], ConfigT
                ],
            ]
        ],
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
    def __init__(self, plugin_id, plugin_config=NoNewPluginConfig, /):
        super().__init__()
        self.id = resolve_plugin_id(plugin_id)
        self.config = plugin_config

    @final
    def __hash__(self):
        return hash((
            self.data().plugin_type,
            self.id,
            NoNewPluginConfig
            if self.config is NoNewPluginConfig
            else dumps(NewPluginPorter._dump_config(self.config)),
        ))

    @final
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return hash(self) == hash(other)

    @final
    async def new(self, services: ServiceLevel, /) -> PluginT:
        """
        Create a new instance of the configured plugin.
        """
        definition = await services.plugins[self.data().plugin_type][self.id]
        args = (definition.cls, services)
        if self.config is not NoNewPluginConfig:
            if not isinstance(definition, ConfigurablePluginDefinition):
                # @todo Add args and such
                raise NotConfigurable
            if not isinstance(self.config, Data):
                self.config = definition.config_cls.data().porter.load(self.config)
            args += self.config
        return await new(*args)

    @final
    @classmethod
    def resolve(cls, factory: ConfigurablePluginFactory[PluginT, Self, Data]) -> Self:
        """
        Resolve a value to an instance of ``self``.
        """
        if isinstance(factory, cls):
            return factory
        return cls(resolve_plugin_id(factory))

    @final
    @override
    @classmethod
    def samples(cls) -> Samples[Self]:
        return Samples([
            lambda: Sample(
                cls("my-first-plugin-id"),
                label="Minimal",
                size=Size.MINIMAL,
            ),
            lambda: Sample(
                cls(
                    "my-first-plugin-id",
                    {
                        "configuration-key": "configuration-value",
                    },
                ),
                label="Full",
                size=Size.FULL,
            ),
        ])


@final
class NewPluginPorter[NewPluginT: NewPlugin](KeyedPorter[NewPluginT]):
    """
    Port :py:class:`betty.plugin.cls.factory.NewPlugin` to portable data.
    """

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
        return self._cls(record["id"], record.get("config", NoNewPluginConfig))

    _load_keyed = assert_mapping()

    @override
    def load_keyed(self, key: str, data: PortableData, /) -> NewPluginT:
        return self.load({**self._load_keyed(data), "id": key})

    @classmethod
    def _dump_config(cls, config: Data | PortableData) -> PortableData:
        if isinstance(config, Data):
            return config.data().porter.dump(config)
        return config

    @override
    def dump(self, data: NewPluginT, /) -> PortableData:
        if data.config is NoNewPluginConfig:
            return data.id
        return {
            "id": data.id,
            "config": self._dump_config(data.config),
        }

    @override
    def dump_keyed(self, data: NewPluginT, /) -> tuple[str, PortableData]:
        return data.id, {} if data.config is NoNewPluginConfig else {
            "config": self._dump_config(data.config)
        }


@final
class NewPluginDefinition[PluginDefinitionT: ClassedPluginDefinition, PluginT](
    ObjectDefinition[NewPlugin[PluginDefinitionT, PluginT]]
):
    """
    Define a plugin factory.
    """

    def __init__(
        self,
        plugin_type: type[
            Intersection[PluginDefinitionT, ClassedPluginDefinition[PluginT]]
        ],
        /,
    ):
        super().__init__(
            label=plugin_type.type().label,
            porter=lambda definition: NewPluginPorter(definition.cls),
        )
        self.plugin_type: Final[type[PluginDefinitionT]] = plugin_type
