from typing import Self, override

from betty.assertions.str import assert_str
from betty.portable import Portable, PortableData
from betty.porters.portable import PortablePorter


class PortablePorterTestPortable(Portable):
    def __init__(self, value: str):
        self.value = value

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        return cls(assert_str()(portable))

    @override
    def dump(self) -> PortableData:
        return self.value


class TestPortablePorter:
    def test_load(self) -> None:
        sut = PortablePorter(PortablePorterTestPortable)
        value = "Hello, world!"
        assert sut.load(value).value == value

    def test_dump(self) -> None:
        sut = PortablePorter(PortablePorterTestPortable)
        value = "Hello, world!"
        assert sut.dump(PortablePorterTestPortable(value)) == value
