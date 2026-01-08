from typing import Self

from typing_extensions import override

from betty.assertion import assert_str
from betty.portable import CallbackPorter, Portable, PortableData, PortablePorter


class TestCallbackPorter:
    def test_load(self) -> None:
        sut = CallbackPorter(lambda _: "loaded", lambda _: "dumped")
        assert sut.load(None) == "loaded"

    def test_dump(self) -> None:
        sut = CallbackPorter(lambda _: "loaded", lambda _: "dumped")
        assert sut.dump(None) == "dumped"


class PortablePorterTestPortable(Portable):
    def __init__(self, value: str):
        self.value = value

    @override
    @classmethod
    def load(cls, serialized: PortableData, /) -> Self:
        return cls(assert_str()(serialized))

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
