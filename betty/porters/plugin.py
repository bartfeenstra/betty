from abc import abstractmethod
from typing import ClassVar, final, override

from typing_extensions import sentinel

from betty.assertions.if_else import assert_if_else
from betty.assertions.mapping import assert_mapping
from betty.assertions.record import Field, assert_record
from betty.data import Data
from betty.functools import Pipeline
from betty.machine_name import MachineName
from betty.plugin.cls.factory import PluginManufacturer
from betty.portable import KeyedPorter, PortableData

NoData = sentinel("NoData")


class PluginPorter[PluginManufacturerT: PluginManufacturer](
    KeyedPorter[PluginManufacturerT]
):
    _data_name: ClassVar[str]

    def __init__(self, cls: type[PluginManufacturerT], /):
        self._cls = cls

    __load = assert_if_else(
        Pipeline(MachineName.definition.porter.load)
        | (lambda plugin_id: {"plugin": plugin_id}),
        assert_record(
            Field("id", MachineName.definition.porter.load),
            Field(_data_name, optional=True),
        ),
    )

    @final
    @override
    def load(self, data: PortableData, /) -> PluginManufacturerT:
        record = self._load(data)
        return self._load(record["id"], record.get(self._data_name, NoData))

    @abstractmethod
    def _load(
        self, plugin_id: MachineName, plugin_data: PortableData | NoData, /
    ) -> PluginManufacturerT:
        pass

    __load_keyed = assert_mapping()

    @final
    @override
    def load_keyed(self, key: str, data: PortableData, /) -> PluginManufacturerT:
        return self.load({**self._load_keyed(data), "id": key})

    @final
    @classmethod
    def dump_plugin_data(cls, data: PluginManufacturerT) -> PortableData:
        if isinstance(data, Data):
            return data.definition.porter.dump(data)
        return data

    @final
    @override
    def dump(self, data: PluginManufacturerT, /) -> PortableData:
        getattr(data, self._data_name)
        if data.config is NoConfig:
            return data.id
        return {
            "id": data.id,
            self._data_name: self.dump_plugin_data(data.config),
        }

    @final
    @override
    def dump_keyed(self, data: PluginManufacturerT, /) -> tuple[str, PortableData]:
        return data.id, {} if data.config is NoConfig else {
            self._data_name: self.dump_config(data.config)
        }
