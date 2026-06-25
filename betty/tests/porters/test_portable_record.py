from typing import Self, override

from betty.datas.aggregate.record import PortableRecord
from betty.indicator.selector import Attr
from betty.portable import PortableData
from betty.porters.portable_record import PortableRecordPorter


class PortableRecordPorterTestPortableRecord(PortableRecord[Attr]):
    def __init__(self, key: str, value: str):
        self.key = key
        self.value = value

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        raise NotImplementedError

    @override
    def dump(self) -> PortableData:
        raise NotImplementedError

    @override
    @classmethod
    def load_key(cls, portable: PortableData, key: Attr, portable_key: str, /) -> Self:
        return cls(portable_key, portable["value"])  # ty:ignore[invalid-argument-type, not-subscriptable]

    @override
    def dump_key(self, key: Attr, /) -> tuple[str, PortableData]:
        return self.key, {"value": self.value}


class TestPortableRecordPorter:
    def test_load_key(self) -> None:
        sut = PortableRecordPorter(PortableRecordPorterTestPortableRecord)
        key = "hello-world"
        value = "Hello, world!"
        data = sut.load_key({"value": value}, Attr("key"), key)
        assert data.key == key
        assert data.value == value

    def test_dump_key(self) -> None:
        sut = PortableRecordPorter(PortableRecordPorterTestPortableRecord)
        key = "hello-world"
        value = "Hello, world!"
        data = PortableRecordPorterTestPortableRecord(key, value)
        assert sut.dump_key(data, Attr("key")) == (key, {"value": value})
