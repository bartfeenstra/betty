from __future__ import annotations

from typing import Never, override

import pytest

from betty.prop import (
    HasProps,
    NotDeletable,
    NotSettable,
    OwnerError,
    Prop,
    PropError,
)


class _PropOwner(HasProps):
    def __init__(self):
        self.init_properties = []
        super().__init__()


class _Value:
    pass


class _Prop(Prop[_PropOwner, tuple[_PropOwner, _Value]]):
    def __init__(self, value: _Value, /):
        self.__value = value

    @override
    def get(self, owner: _PropOwner, /) -> tuple[_PropOwner, _Value]:
        return owner, self.__value

    @override
    def init_owner(self, owner: _PropOwner, /) -> None:
        owner.init_properties.append(self)


class TestHasProps:
    def test___init__(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        owner = _Owner()
        assert _Owner.my_first_prop in owner.init_properties


class TestProp:
    def test_set(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        owner = _Owner()
        with pytest.raises(NotSettable):
            _Owner.my_first_prop.set(
                owner,
                Never,  # ty:ignore[invalid-argument-type]
            )

    def test_delete(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        owner = _Owner()
        with pytest.raises(NotDeletable):
            _Owner.my_first_prop.delete(owner)

    def test___get____with_class(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        assert isinstance(_Owner.my_first_prop, _Prop)
        assert _Owner.my_first_prop is _Owner.my_first_prop

    def test___get____with_instance(self) -> None:
        value = _Value()

        class _Owner(_PropOwner):
            my_first_prop = _Prop(value)

        owner = _Owner()
        assert owner.my_first_prop == (owner, value)

    def test___set__(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        owner = _Owner()
        with pytest.raises(NotSettable):
            owner.my_first_prop = Never  # ty:ignore[invalid-assignment]

    def test___delete__(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        owner = _Owner()
        with pytest.raises(NotDeletable):
            del owner.my_first_prop

    def test_init_owner(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        owner = _Owner()
        assert _Owner.my_first_prop in owner.init_properties

    def test_delete_owner(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        owner = _Owner()
        _Owner.my_first_prop.delete_owner(owner)

    def test_prop(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        assert _Owner.my_first_prop.prop.owner is _Owner
        assert _Owner.my_first_prop.prop.name == "my_first_prop"


class TestPropError:
    def test___init__(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        message = "Hello, world!"
        sut = PropError(_Owner.my_first_prop, message)
        assert str(sut) == message
        assert sut.prop is _Owner.my_first_prop


class TestOwnerError:
    def test___init__(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        owner = _Owner()
        message = "Hello, world!"
        sut = OwnerError(_Owner.my_first_prop, owner, message)
        assert str(sut) == message
        assert sut.obj is owner
        assert sut.name == "my_first_prop"


class TestNotSettable:
    def test___init__(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        sut = NotSettable(_Owner.my_first_prop, _Owner())
        assert "my_first_prop" in str(sut)


class TestNotDeletable:
    def test___init__(self) -> None:
        class _Owner(_PropOwner):
            my_first_prop = _Prop(_Value())

        sut = NotDeletable(_Owner.my_first_prop, _Owner())
        assert "my_first_prop" in str(sut)
