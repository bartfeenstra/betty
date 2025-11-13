import pytest

from betty.mutability import ImmutableError, Mutable, MutableError, immutable, mutable


def test_immutable() -> None:
    instance = Mutable(mutable=True)
    immutable(instance)
    assert instance.immutable


def test_mutable() -> None:
    instance = Mutable(mutable=False)
    mutable(instance)
    assert instance.mutable


class TestMutable:
    @staticmethod
    def _immutable() -> pytest.MarkDecorator:
        return pytest.mark.parametrize(
            "immutable",
            [
                True,
                False,
            ],
        )

    @staticmethod
    def _mutable() -> pytest.MarkDecorator:
        return pytest.mark.parametrize(
            "mutable",
            [
                True,
                False,
            ],
        )

    def test_assert_immutable(self) -> None:
        Mutable(mutable=False).assert_immutable()
        with pytest.raises(MutableError):
            Mutable(mutable=True).assert_immutable()

    def test_assert_mutable(self) -> None:
        Mutable(mutable=True).assert_mutable()
        with pytest.raises(ImmutableError):
            Mutable(mutable=False).assert_mutable()

    def test_get_mutable_instances(self) -> None:
        assert not list(Mutable().get_mutable_instances())

    @_immutable()
    def test_is_immutable__get(self, immutable: bool) -> None:
        assert Mutable(mutable=not immutable).immutable is immutable

    @_immutable()
    def test_immutable__set(self, immutable: bool) -> None:
        sut = Mutable()
        sut.immutable = immutable
        assert sut.immutable is immutable

    @_mutable()
    def test_mutable__get(self, mutable: bool) -> None:
        assert Mutable(mutable=mutable).mutable is mutable

    @_mutable()
    def test_mutable__set(self, mutable: bool) -> None:
        sut = Mutable()
        sut.mutable = mutable
        assert sut.mutable is mutable
