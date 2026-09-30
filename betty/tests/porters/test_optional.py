from betty.porters.callback import CallbackPorter
from betty.porters.optional import OptionalPorter
from betty.validators.str import is_str


class TestOptionalPorter:
    def test_load__without_none(self) -> None:
        sut = OptionalPorter(CallbackPorter(is_str, is_str))
        value = "Hello, world!"
        assert sut.load(value) == value

    def test_load__with_none(self) -> None:
        sut = OptionalPorter(CallbackPorter(is_str, is_str))
        assert sut.load(None) is None

    def test_dump__without_none(self) -> None:
        sut = OptionalPorter(CallbackPorter(is_str, is_str))
        value = "Hello, world!"
        assert sut.dump(value) == value

    def test_dump__with_none(self) -> None:
        sut = OptionalPorter(CallbackPorter(is_str, is_str))
        assert sut.dump(None) is None
