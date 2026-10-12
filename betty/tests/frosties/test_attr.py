from betty.frosties.attr import AttrFreezable


class TestAttrFreezable:
    def test_is_frozen(self) -> None:
        assert not AttrFreezable().is_frozen

    def test_freeze(self) -> None:
        sut = AttrFreezable()
        sut.freeze()
        assert sut.is_frozen
