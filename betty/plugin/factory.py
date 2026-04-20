"""
Plugin factories.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, MutableSequence
from functools import cache
from json import dumps
from typing import TYPE_CHECKING, Self, TypeVar, final, override

from betty.assertion import (
    AssertionChain,
    OptionalField,
    RequiredField,
    assert_mapping,
    assert_or,
    assert_record,
)
from betty.data import Data, DataDefinition
from betty.data.aggregate.record import PortableRecord, RecordDefinition
from betty.data.aggregate.record.object import AttrDefinition, ObjectDefinition
from betty.data.indicator.selector import Attr
from betty.exception import HumanFacingException
from betty.factory import DataManufacturable, FactoryError
from betty.importlib import fully_qualified_name
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName
from betty.plugin import PluginDefinition
from betty.plugin.cls import Plugin
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.sample import Samplable, Sample, Samples, Size
from betty.typing import Void, VoidType

if TYPE_CHECKING:
    from betty.portable import PortableData
    from betty.service_level import ServiceLevel


class PluginManufacturerError(HumanFacingException, FactoryError):
    """
    Raised when a plugin manufacturer could not create a new plugin instance.
    """


_PluginManufacturerPluginT = TypeVar(
    "_PluginManufacturerPluginT", bound=Plugin, covariant=True
)
_PluginManufacturerPluginDefinitionT = TypeVar(
    "_PluginManufacturerPluginDefinitionT", bound=PluginDefinition
)


class PluginManufacturer[
    PluginManufacturerPluginDefinitionT: PluginDefinition,
    PluginManufacturerPluginT: Plugin,
](PortableRecord[Attr], Samplable, Data[RecordDefinition], ABC):
    """
    Configure a single plugin instance.
    """

    @final
    def __init__(
        self,
        plugin: ResolvablePluginId[_PluginManufacturerPluginDefinitionT],
        data: Data | PortableData | VoidType = Void,
        /,
    ):
        super().__init__()
        self._plugin_id = resolve_plugin_id(plugin)
        self._plugin_data = data

    @final
    def __hash__(self):
        return hash((
            self.plugin_type(),
            self.plugin_id,
            Void
            if self.plugin_data is Void
            else dumps(
                self.plugin_data.data().porter.dump(self.plugin_data)
                if isinstance(self.plugin_data, Data)
                else self.plugin_data,
            ),
        ))

    @classmethod
    @abstractmethod
    def plugin_type(cls) -> type[_PluginManufacturerPluginDefinitionT]:
        """
        The type of plugin that can be manufactured.
        """

    @final
    @override
    @classmethod
    @cache
    def data(cls) -> ObjectDefinition[Self]:
        return ObjectDefinition(cls, label=cls.plugin_type().type().label)

    @final
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return hash(self) == hash(other)

    @final
    @property
    @AttrDefinition(MachineName)
    def plugin_id(self) -> MachineName:
        """
        The plugin ID.
        """
        return self._plugin_id

    @final
    @property
    @AttrDefinition(DataDefinition(cls=object, label=_("Data")))
    def plugin_data(self) -> Data | PortableData | VoidType:
        """
        Get the plugin's own data.
        """
        return self._plugin_data

    @final
    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        record = assert_or(
            AssertionChain(MachineName.load)
            | (lambda plugin_id: {"plugin": plugin_id}),
            assert_record(
                RequiredField("plugin", MachineName.load),
                OptionalField("data"),
            ),
        )(portable)
        return cls(record["plugin"], record.get("data", Void))

    @final
    @override
    @classmethod
    def load_key(cls, portable: PortableData, key: Attr, portable_key: str, /) -> Self:
        return cls.load({**assert_mapping()(portable), "plugin": portable_key})

    @final
    def _dump_data(self, configuration: Data | PortableData) -> PortableData:
        if isinstance(configuration, Data):
            return configuration.data().porter.dump(configuration)
        return configuration

    @final
    @override
    def dump(self) -> PortableData:
        data = self.plugin_data
        if data is Void:
            return self._plugin_id
        return {
            "plugin": self._plugin_id,
            "data": self._dump_data(data),
        }

    @final
    @override
    def dump_key(self, key: Attr, /) -> tuple[str, PortableData]:
        return self.plugin_id, {} if self.plugin_data is Void else {
            "data": self._dump_data(self.plugin_data)
        }

    @final
    async def __call__(self, services: ServiceLevel, /) -> _PluginManufacturerPluginT:
        """
        Create a new instance of the configured plugin.
        """
        plugin_cls = (await services.plugins[self.plugin_type()][self.plugin_id]).cls
        if self.plugin_data is Void:
            return await services.factory.new(plugin_cls)
        if not issubclass(plugin_cls, DataManufacturable):
            raise PluginManufacturerError(
                _(
                    '"{target}" is not configurable, but configuration was given.'
                ).format(target=fully_qualified_name(plugin_cls))
            )
        plugin_data = self.plugin_data
        if not isinstance(plugin_data, Data):
            plugin_data = plugin_cls.new_data_cls().data().porter.load(plugin_data)
        return await plugin_cls.new(services, plugin_data)

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
            return [manufacturers]
        if (
            isinstance(manufacturers, (str, PluginDefinition))
            or isinstance(manufacturers, type)
            and issubclass(manufacturers, Plugin)
        ):
            return [cls.resolve(manufacturers)]
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
                    },
                ),
                label="Full",
                size=Size.FULL,
            ),
        ])


type ResolvablePluginManufacturer[
    PluginDefinitionT: PluginDefinition,
    PluginT: Plugin,
] = (
    ResolvablePluginId[PluginDefinitionT]
    | PluginManufacturer[PluginDefinitionT, PluginT]
)


type ResolvablePluginManufacturerSequence[
    PluginDefinitionT: PluginDefinition,
    PluginT: Plugin,
] = (
    ResolvablePluginManufacturer[PluginDefinitionT, PluginT]
    | Iterable[ResolvablePluginManufacturer[PluginDefinitionT, PluginT]]
)
