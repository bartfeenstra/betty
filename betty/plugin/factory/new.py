from __future__ import annotations

from json import dumps
from typing import Final, Self, final, overload, override

from typing_extensions import disjoint_base, sentinel

from betty.assertions.if_else import assert_if_else
from betty.assertions.mapping import assert_mapping
from betty.assertions.record import Field, assert_record
from betty.attrs.machine_name import new_machine_name_attr
from betty.attrs.owner import OwnerAttr
from betty.classtools import TypeABCMeta
from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
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

# @todo Move this onto NewPlugin?
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
