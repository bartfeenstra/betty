import pytest

from betty.mutability import ImmutableError, Mutable, MutableError, immutable, mutable


def test_immutable() -> None:
    instance = Mutable(mutable=True)
    immutable(instance)
    assert instance.is_immutable


def test_mutable() -> None:
    instance = Mutable(mutable=False)
    mutable(instance)
    assert instance.is_mutable


class TestMutable:
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

    def test_immutable(self) -> None:
        sut = Mutable(mutable=True)
        sut.immutable()
        assert sut.is_immutable

    def test_is_immutable(self) -> None:
        assert Mutable(mutable=False).is_immutable
        assert not Mutable(mutable=True).is_immutable

    def test_is_mutable(self) -> None:
        assert Mutable(mutable=True).is_mutable
        assert not Mutable(mutable=False).is_mutable

    def test_mutable(self) -> None:
        sut = Mutable(mutable=False)
        sut.mutable()
        assert sut.is_mutable
