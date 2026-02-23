"""
Plugin factories.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, MutableSequence
from functools import cache
from json import dumps
from typing import TYPE_CHECKING, Any, Self, TypeVar, final, override

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
from betty.locale.localizable.gettext import _
from betty.machine_name import MachineName
from betty.plugin import Plugin, PluginDefinition, ResolvableId, resolve_id
from betty.sample import Samplable, Sample, Samples, Size
from betty.typing import Void, VoidType

if TYPE_CHECKING:
    import builtins

    from betty.portable import PortableData
    from betty.service.level import ServiceLevel

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
        plugin: ResolvableId[_PluginManufacturerPluginDefinitionT],
        data: Data | PortableData | VoidType = Void,
        /,
    ):
        super().__init__()
        self._plugin_id = resolve_id(plugin)
        self._plugin_data = data

    @final
    def __hash__(self):
        return hash(
            (
                self.type(),
                self.plugin_id,
                Void
                if self.plugin_data is Void
                else dumps(
                    self.plugin_data.data().porter.dump(self.plugin_data)
                    if isinstance(self.plugin_data, Data)
                    else self.plugin_data,
                ),
            )
        )

    @classmethod
    @abstractmethod
    def type(cls) -> builtins.type[_PluginManufacturerPluginDefinitionT]:
        """
        The type of plugin that can be manufactured.
        """

    @final
    @override
    @classmethod
    @cache
    def data(cls) -> ObjectDefinition[Self]:
        return ObjectDefinition(cls, label=cls.type().type().label)

    @final
    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.plugin_id, self.plugin_data) == (
            other.plugin_id,
            other.plugin_data,
        )

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
        return await services.factory.new(
            (await services.plugins[self.type()][self.plugin_id]).cls,
            self.plugin_data,
        )

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
        if (
            isinstance(manufacturer, (PluginDefinition, str))
            or isinstance(manufacturer, type)
            and issubclass(manufacturer, Plugin)
        ):
            return cls(
                resolve_id(
                    manufacturer,  # ty:ignore[invalid-argument-type]
                )
            )
        return manufacturer

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
        return list(map(cls.resolve, manufacturers))  # ty:ignore[invalid-argument-type]

    @final
    @override
    @classmethod
    def samples(cls) -> Samples[Self]:
        return Samples(
            [
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
            ]
        )


type ResolvablePluginManufacturer[
    PluginDefinitionT: PluginDefinition,
    PluginT: Plugin,
] = ResolvableId[PluginDefinitionT] | PluginManufacturer[PluginDefinitionT, PluginT]


type ResolvablePluginManufacturerSequence[
    PluginDefinitionT: PluginDefinition,
    PluginT: Plugin,
] = (
    ResolvablePluginManufacturer[PluginDefinitionT, PluginT]
    | Iterable[ResolvablePluginManufacturer[PluginDefinitionT, PluginT]]
)
