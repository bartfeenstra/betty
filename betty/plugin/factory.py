"""
Plugin factories.
"""

from __future__ import annotations

from collections.abc import Iterable, MutableSequence
from json import dumps
from typing import TYPE_CHECKING, Final, Generic, Never, Self, TypeVar, final, override

from betty.assertions.if_else import assert_if_else
from betty.assertions.mapping import assert_mapping
from betty.assertions.record import Field, assert_record
from betty.attrs.machine_name import new_machine_name_attr
from betty.attrs.owner import OwnerAttr
from betty.classtools import TypeABCMeta
from betty.data import Data, DataDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.definition.cls import OnSetCls
from betty.exception import HumanFacingException
from betty.factory import DataManufacturable, FactoryError
from betty.freezer import Frozen
from betty.functools import Pipeline
from betty.importlib import fully_qualified_name
from betty.localizables.gettext import _
from betty.machine_name import MachineName
from betty.nothing import Nothing, NothingType
from betty.plugin import PluginDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.portable import KeyedPorter, PortableData
from betty.prop import HasProps
from betty.sample import Samplable, Sample, Samples, Size

if TYPE_CHECKING:
    from betty.service_level import ServiceLevel
    from betty.typing import Intersection


class PluginManufacturerError(HumanFacingException, FactoryError):
    """
    Raised when a plugin manufacturer could not create a new plugin instance.
    """


_PluginManufacturerPluginT = TypeVar("_PluginManufacturerPluginT", covariant=True)
_PluginManufacturerPluginDefinitionT = TypeVar(
    "_PluginManufacturerPluginDefinitionT", bound=PluginClsDefinition
)


class PluginManufacturer(
    Samplable,
    Data["PluginManufacturerDefinition"],
    HasProps,
    Frozen,
    Generic[_PluginManufacturerPluginDefinitionT, _PluginManufacturerPluginT],  # noqa: UP046
    metaclass=TypeABCMeta,
):
    """
    Configure a single plugin instance.
    """

    plugin_id = new_machine_name_attr()
    """
    The plugin ID.
    """

    plugin_data = OwnerAttr(
        DataDefinition[Data | PortableData | NothingType](label=_("Data"))
    )
    """
    Get the plugin's own data.
    """

    @final
    def __init__(
        self,
        plugin: ResolvablePluginId[_PluginManufacturerPluginDefinitionT],
        data: Data | PortableData | NothingType = Nothing,
        /,
    ):
        super().__init__()
        self.plugin_id = resolve_plugin_id(plugin)
        self.plugin_data = data

    @final
    def __hash__(self):
        return hash((
            self.data().plugin_type,
            self.plugin_id,
            Nothing
            if self.plugin_data is Nothing
            else dumps(PluginManufacturerPorter._dump_data(self.plugin_data)),
        ))

    @final
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return hash(self) == hash(other)

    @final
    async def __call__(self, services: ServiceLevel, /) -> _PluginManufacturerPluginT:
        """
        Create a new instance of the configured plugin.
        """
        plugin_cls = (
            await services.plugins[self.data().plugin_type][self.plugin_id]
        ).cls  # ty:ignore[unresolved-attribute]
        if self.plugin_data is Nothing:
            return await services.factory.new(plugin_cls)
        if not issubclass(plugin_cls, DataManufacturable):
            raise PluginManufacturerError(
                _("{target} is not configurable, but configuration was given.").format(
                    target=fully_qualified_name(plugin_cls)
                )
            )
        plugin_data = self.plugin_data
        if not isinstance(plugin_data, Data):
            plugin_data = plugin_cls.new_data_cls().data().porter.load(plugin_data)
        return await plugin_cls.new(services, plugin_data)

    @final
    @classmethod
    def resolve(
        cls,
        manufacturer: ResolvablePluginManufacturer[
            _PluginManufacturerPluginDefinitionT, _PluginManufacturerPluginT
        ],
    ) -> PluginManufacturer[
        _PluginManufacturerPluginDefinitionT, _PluginManufacturerPluginT
    ]:
        """
        Resolve a value to a plugin manufacturer.
        """
        try:
            return cls(resolve_plugin_id(manufacturer))
        except ValueError:
            return manufacturer  # ty:ignore[invalid-return-type]

    @final
    @classmethod
    def resolve_sequence(
        cls,
        manufacturers: ResolvablePluginManufacturerSequence[
            _PluginManufacturerPluginDefinitionT, _PluginManufacturerPluginT
        ],
    ) -> MutableSequence[
        PluginManufacturer[
            _PluginManufacturerPluginDefinitionT, _PluginManufacturerPluginT
        ]
    ]:
        """
        Resolve a value to a sequence of plugin manufacturers.
        """
        if isinstance(manufacturers, PluginManufacturer):
            return [manufacturers]  # ty:ignore[invalid-return-type]
        if (
            isinstance(manufacturers, (str, PluginDefinition))
            or isinstance(manufacturers, type)
            and issubclass(manufacturers, Plugin)
        ):
            return [cls.resolve(manufacturers)]  # ty:ignore[invalid-argument-type]
        return list(map(cls.resolve, manufacturers))

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
                    },  # ty:ignore[invalid-argument-type]
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
            Field("plugin", MachineName.data().porter.load),
            Field("data", optional=True),
        ),
    )

    @override
    def load(self, data: PortableData, /) -> PluginManufacturerT:
        record = self._load(data)
        return self._cls(record["plugin"], record.get("data", Nothing))

    _load_keyed = assert_mapping()

    @override
    def load_keyed(self, key: str, data: PortableData, /) -> PluginManufacturerT:
        return self.load({**self._load_keyed(data), "plugin": key})

    @classmethod
    def _dump_data(cls, configuration: Data | PortableData) -> PortableData:
        if isinstance(configuration, Data):
            return configuration.data().porter.dump(configuration)
        return configuration

    @override
    def dump(self, data: PluginManufacturerT, /) -> PortableData:
        plugin_data = data.plugin_data
        if plugin_data is Nothing:
            return data.plugin_id
        return {
            "plugin": data.plugin_id,
            "data": self._dump_data(plugin_data),
        }

    @override
    def dump_keyed(self, data: PluginManufacturerT, /) -> tuple[str, PortableData]:
        return data.plugin_id, {} if data.plugin_data is Nothing else {
            "data": self._dump_data(data.plugin_data)
        }


@final
class PluginManufacturerDefinition[PluginDefinitionT: PluginClsDefinition, PluginT](
    ObjectDefinition[
        PluginManufacturer[PluginDefinitionT, PluginT],
        Never,
        KeyedPorter[PluginManufacturer[PluginDefinitionT, PluginT]],
    ]
):
    """
    Define a plugin manufacturer.
    """

    def __init__(
        self,
        plugin_type: type[
            Intersection[PluginDefinitionT, PluginClsDefinition[PluginT]]
        ],
        /,
    ):
        super().__init__(
            label=plugin_type.type().label,
            porter=OnSetCls(
                lambda definition: PluginManufacturerPorter(definition.cls)
            ),
        )
        self.plugin_type: Final[type[PluginDefinition]] = plugin_type


type ResolvablePluginManufacturer[PluginDefinitionT: PluginClsDefinition, PluginT] = (
    ResolvablePluginId[PluginDefinitionT]
    | PluginManufacturer[PluginDefinitionT, PluginT]
)


type ResolvablePluginManufacturerSequence[
    PluginDefinitionT: PluginClsDefinition,
    PluginT,
] = (
    ResolvablePluginManufacturer[PluginDefinitionT, PluginT]
    | Iterable[ResolvablePluginManufacturer[PluginDefinitionT, PluginT]]
)
