from betty.typing import Unreachable, is_lambda


class TestUnreachable:
    def test(self) -> None:
        assert str(Unreachable())

    def test__with_reason(self) -> None:
        assert ", because I did an oopsie." in str(Unreachable("I did an oopsie"))


def _not_a_lambda() -> None:
    pass


def test_is_lambda() -> None:
    assert is_lambda(lambda: None)
    assert not is_lambda(_not_a_lambda)
