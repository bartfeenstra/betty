"""
Classed plugins.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from json import dumps
from typing import TYPE_CHECKING, Any, Final, Self, final, overload, override

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
from betty.definition.cls import ClassedDefinition
from betty.exception import HumanFacingException
from betty.factory import Manufacturable
from betty.freezer import Frozen
from betty.functools import Pipeline
from betty.importlib import fully_qualified_name
from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.machine_name import MachineName, ResolvableMachineName
from betty.plugin import PluginDefinition
from betty.plugin.resolve import (
    ResolvablePluginDefinition,
    ResolvablePluginId,
    ResolvablePluginTypeDefinition,
    resolve_plugin_id,
    resolve_plugin_type_definition,
)
from betty.portable import KeyedPorter, PortableData
from betty.prop import HasProps
from betty.sample import Samplable, Sample, Samples, Size
from betty.service_level import Integratable, ServiceLevel

if TYPE_CHECKING:
    from collections.abc import Callable, MutableMapping


class Plugin[PluginDefinitionT: ClassedPluginDefinition]:
    """
    A plugin class.

    Classed plugins may optionally subclass this class to expose their plugin definitions.
    """

    @final
    @classmethod
    def plugin(cls) -> PluginDefinitionT:
        """
        The plugin definition.
        """
        try:
            return _plugins[cls]  # ty:ignore[invalid-return-type]
        except KeyError:  # pragma: no cover
            raise NotImplementedError(
                f"{fully_qualified_name(cls)} was not decorated with a {fully_qualified_name(ClassedPluginDefinition)} subclass."
            ) from None


class ClassedPluginDefinition[PluginT = Any](
    ClassedDefinition[PluginT], PluginDefinition
):
    """
    A classed plugin definition.
    """

    @override
    def _set_cls(self, cls: type[PluginT], /) -> None:
        super()._set_cls(cls)
        if issubclass(cls, Plugin):
            _plugins[cls] = self


_plugins: Final[MutableMapping[type, ClassedPluginDefinition[Any]]] = {}


class _Configurable[ConfigurationT: Data]:
    """
    A configurable plugin.

    This internal base class exists only to ensure that multiple manufacturable base classes can be subclasses, but
    only for the same configuration type.
    """


class ConfigurableManufacturable[ConfigurationT: Data](
    _Configurable[ConfigurationT], metaclass=ABCMeta
):
    """
    A plugin that can be initialized asynchronously from configuration data.
    """

    @classmethod
    @abstractmethod
    async def new(cls, configuration: ConfigurationT, /) -> Self:
        """
        Create a new instance.
        """


class ConfigurableIntegratable[ConfigurationT: Data](
    _Configurable[ConfigurationT], metaclass=ABCMeta
):
    """
    A plugin that can be initialized asynchronously for a service level from configuration data.
    """

    @classmethod
    @abstractmethod
    async def new(
        cls, services: ServiceLevel, configuration: ConfigurationT, /
    ) -> Self:
        """
        Create a new instance.
        """


type ManufacturablePlugin[PluginT] = (
    Intersection[PluginT, Manufacturable] | Intersection[PluginT, Callable[[], PluginT]]
)


type IntegrablePlugin[PluginT] = (
    Intersection[PluginT, Integratable] | ManufacturablePlugin[PluginT]
)


type ConfigurablePlugin[PluginT, ConfigurationT: Data] = Intersection[
    PluginT,
    ConfigurableIntegratable[ConfigurationT]
    | ConfigurableManufacturable[ConfigurationT],
]


type PluginFactory[PluginT, PluginManufacturerT: PluginManufacturer] = (
    type[IntegrablePlugin[PluginT] | ManufacturablePlugin[PluginT]]
    | PluginManufacturerT
)


type ConfigurablePluginFactory[
    PluginT,
    PluginManufacturerT: PluginManufacturer,
    ConfigurationT: Data,
] = type[ConfigurablePlugin[PluginT, ConfigurationT]] | PluginManufacturerT


type AnyPluginFactory[PluginT, PluginManufacturerT: PluginManufacturer] = (
    ConfigurablePluginFactory[PluginT, PluginManufacturerT, Data]
    | PluginFactory[PluginT, PluginManufacturerT]
)


class ConfigurablePluginDefinition[PluginT, ConfigurationT: Data](
    ClassedPluginDefinition[ConfigurablePlugin[PluginT, ConfigurationT]]
):
    """
    A configurable plugin definition.
    """

    def __init__(
        self,
        *args: Any,
        configuration_cls: type[ConfigurationT] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.__configuration_cls = configuration_cls

    @property
    def configuration_cls(self) -> type[ConfigurationT]:
        """
        The plugin's configuration class, if it is configurable.
        """
        if not self.__configuration_cls:
            raise NotConfigurable
        return self.__configuration_cls


@final
class NotConfigurable(HumanFacingException):
    """
    Raised when a plugin is not configurable.
    """

    def __init__[PluginDefinitionT: PluginDefinition](
        self,
        plugin_type: ResolvablePluginTypeDefinition[PluginDefinitionT],
        plugin_id: ResolvablePluginId[PluginDefinitionT],
        /,
    ):
        super().__init__(
            _("{plugin_type} {plugin} is not configurable").format(
                plugin_type=resolve_plugin_type_definition(plugin_type).label,
                plugin=Quote(resolve_plugin_id(plugin_id)),
            )
        )


@overload
async def new[PluginT, PluginManufacturerT: PluginManufacturer](
    plugin: PluginFactory[PluginT, PluginManufacturerT],
    services: ServiceLevel,
    /,
) -> PluginT:
    pass


@overload
async def new[PluginT, PluginManufacturerT: PluginManufacturer, ConfigurationT: Data](
    plugin: ConfigurablePluginFactory[PluginT, PluginManufacturerT, ConfigurationT],
    services: ServiceLevel,
    configuration: ConfigurationT,
    /,
) -> PluginT:
    pass


async def new(manufacturer, services, configuration=None, /):
    """
    Initialize a plugin.
    """
    if configuration is None:
        if issubclass(manufacturer, Integratable):
            return await manufacturer.new(services)
        if issubclass(manufacturer, Manufacturable):
            return await manufacturer.new()
        return await manufacturer()
    if issubclass(manufacturer, ConfigurableIntegratable):
        return await manufacturer.new(services, configuration)
    return await manufacturer.new(configuration)


NoPluginConfiguration = sentinel("NoPluginConfiguration")


@disjoint_base
class PluginManufacturer[PluginDefinitionT: ClassedPluginDefinition, PluginT](
    Samplable,
    Data["PluginManufacturerDefinition[PluginDefinitionT, PluginT]"],
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

    configuration = OwnerAttr(
        DataDefinition[Data | PortableData | NoPluginConfiguration](
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
    def __init__[ConfigurationT: Data](
        self,
        plugin_id: ResolvablePluginDefinition[
            Intersection[
                PluginDefinitionT,
                ConfigurablePluginDefinition[
                    ConfigurablePlugin[PluginT, ConfigurationT], ConfigurationT
                ],
            ]
        ],
        plugin_configuration: ConfigurationT,
        /,
    ):
        pass

    @overload
    def __init__[ConfigurationT: Data](
        self, plugin_id: ResolvableMachineName, plugin_configuration: PortableData, /
    ):
        pass

    @final
    def __init__(self, plugin_id, plugin_configuration=NoPluginConfiguration, /):
        super().__init__()
        self.id = resolve_plugin_id(plugin_id)
        self.configuration = plugin_configuration

    @final
    def __hash__(self):
        return hash((
            self.data().plugin_type,
            self.id,
            NoPluginConfiguration
            if self.configuration is NoPluginConfiguration
            else dumps(
                PluginManufacturerPorter._dump_configuration(self.configuration)
            ),
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
        plugin_cls = (await services.plugins[self.data().plugin_type][self.id]).cls
        args = (plugin_cls, services)
        if self.configuration is not NoPluginConfiguration:
            if not issubclass(plugin_cls, ConfigurablePlugin.__value__):
                raise NotConfigurable(self.data().plugin_type, self.id)
            configuration = self.configuration
            if not isinstance(configuration, Data):
                configuration = (
                    plugin_cls.configuration_cls().data().porter.load(configuration)
                )
            args += configuration
        return await new(*args)

    @final
    @classmethod
    def resolve(
        # @todo Any
        cls,
        manufacturer: ConfigurablePluginFactory[PluginT, Self, Data],
    ) -> Self:
        """
        Resolve a value to a plugin manufacturer.
        """
        if isinstance(manufacturer, cls):
            return manufacturer
        return cls(resolve_plugin_id(manufacturer))

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
class PluginManufacturerPorter[PluginManufacturerT: PluginManufacturer](
    KeyedPorter[PluginManufacturerT]
):
    """
    Port :py:class:`betty.plugin.factory.PluginManufacturer` to portable data.
    """

    def __init__(self, cls: type[PluginManufacturerT]):
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
    def load(self, data: PortableData, /) -> PluginManufacturerT:
        record = self._load(data)
        return self._cls(record["id"], record.get("config", NoPluginConfiguration))

    _load_keyed = assert_mapping()

    @override
    def load_keyed(self, key: str, data: PortableData, /) -> PluginManufacturerT:
        return self.load({**self._load_keyed(data), "id": key})

    @classmethod
    def _dump_configuration(cls, configuration: Data | PortableData) -> PortableData:
        if isinstance(configuration, Data):
            return configuration.data().porter.dump(configuration)
        return configuration

    @override
    def dump(self, data: PluginManufacturerT, /) -> PortableData:
        configuration = data.configuration
        if configuration is NoPluginConfiguration:
            return data.id
        return {
            "id": data.id,
            "config": self._dump_configuration(configuration),
        }

    @override
    def dump_keyed(self, data: PluginManufacturerT, /) -> tuple[str, PortableData]:
        return data.id, {} if data.configuration is NoPluginConfiguration else {
            "config": self._dump_configuration(data.configuration)
        }


@final
class PluginManufacturerDefinition[PluginDefinitionT: ClassedPluginDefinition, PluginT](
    ObjectDefinition[PluginManufacturer[PluginDefinitionT, PluginT]]
):
    """
    Define a plugin manufacturer.
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
            porter=lambda definition: PluginManufacturerPorter(definition.cls),
        )
        self.plugin_type: Final[type[PluginDefinitionT]] = plugin_type
