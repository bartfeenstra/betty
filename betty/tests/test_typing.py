from betty.typing import Unreachable


class TestUnreachable:
    def test(self) -> None:
        assert str(Unreachable())

    def test__with_reason(self) -> None:
        assert ", because I did an oopsie." in str(Unreachable("I did an oopsie"))
