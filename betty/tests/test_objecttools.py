import pytest

from betty.objecttools import AttrOperators


class TestAttrOperators:
    class _Object:
        pass

    class _Value:
        pass

    sut = AttrOperators("_my_first_attr")

    def test_name(self) -> None:
        assert self.sut.name == "_my_first_attr"

    def test_has(self) -> None:
        owner = self._Object()
        assert not self.sut.has(owner)
        owner._my_first_attr = self._Value()  # ty:ignore[unresolved-attribute]
        assert self.sut.has(owner)

    def test_get(self) -> None:
        owner = self._Object()
        with pytest.raises(AttributeError):
            self.sut.get(owner)
        value = self._Value()
        owner._my_first_attr = value  # ty:ignore[unresolved-attribute]
        assert self.sut.get(owner) is value

    def test_set(self) -> None:
        owner = self._Object()
        value = self._Value()
        self.sut.set(owner, value)
        assert owner._my_first_attr is value  # ty:ignore[unresolved-attribute]

    def test_delete(self) -> None:
        owner = self._Object()
        with pytest.raises(AttributeError):
            self.sut.delete(owner)
        owner._my_first_attr = self._Value()  # ty:ignore[unresolved-attribute]
        self.sut.delete(owner)
        assert not hasattr(owner, "_my_first_attr")
