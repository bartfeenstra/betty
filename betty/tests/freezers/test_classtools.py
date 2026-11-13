from betty.freezers.classtools import FrozenOnInit
from betty.frozen import is_frozen


class TestFrozenOnInit:
    def test__is_frozen(self) -> None:
        assert is_frozen(FrozenOnInit())

    def test_is_frozen(self) -> None:
        assert FrozenOnInit().is_frozen
