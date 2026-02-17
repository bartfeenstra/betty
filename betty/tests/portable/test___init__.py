from typing import Self, override

from betty.assertion import assert_str
from betty.portable import (
    CallbackPorter,
    OptionalPorter,
    Portable,
    PortableData,
    PortablePorter,
)


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


class TestOptionalPorter:
    def test_load__without_none(self) -> None:
        sut = OptionalPorter(CallbackPorter(assert_str(), assert_str()))
        value = "Hello, world!"
        assert sut.load(value) == value

    def test_load__with_none(self) -> None:
        sut = OptionalPorter(CallbackPorter(assert_str(), assert_str()))
        assert sut.load(None) is None

    def test_dump__without_none(self) -> None:
        sut = OptionalPorter(CallbackPorter(assert_str(), assert_str()))
        value = "Hello, world!"
        assert sut.dump(value) == value

    def test_dump__with_none(self) -> None:
        sut = OptionalPorter(CallbackPorter(assert_str(), assert_str()))
        assert sut.dump(None) is None
