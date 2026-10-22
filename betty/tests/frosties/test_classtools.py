from betty.frosties.classtools import Frozen
from betty.frosty import is_frozen


class TestFrozen:
    def test__is_frozen(self) -> None:
        assert is_frozen(Frozen())

    def test_is_frozen(self) -> None:
        assert Frozen().is_frozen
