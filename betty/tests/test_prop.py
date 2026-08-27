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
    @override
    def _pre_init(self) -> None:
        self.pre_init_properties = []
        super()._pre_init()

    @override
    def _post_init(self) -> None:
        self.post_init_properties = []
        super()._post_init()


class _Value:
    pass


class _Prop(Prop[_PropOwner, tuple[_PropOwner, _Value]]):
    def __init__(self, value: _Value | None = None, /):
        self.__value = value or _Value()

    @override
    def get(self, owner: _PropOwner, /) -> tuple[_PropOwner, _Value]:
        return owner, self.__value

    @override
    def pre_init_owner(self, owner: _PropOwner, /) -> None:
        owner.pre_init_properties.append(self)

    @override
    def post_init_owner(self, owner: _PropOwner, /) -> None:
        owner.post_init_properties.append(self)


class _Owner(_PropOwner):
    my_first_prop = _Prop()


class TestHasProps:
    def test___init__(self) -> None:
        owner = _Owner()
        assert _Owner.my_first_prop in owner.pre_init_properties
        assert _Owner.my_first_prop in owner.post_init_properties


class TestProp:
    def test_set(self) -> None:
        owner = _Owner()
        with pytest.raises(NotSettable):
            _Owner.my_first_prop.set(
                owner,
                Never,  # ty:ignore[invalid-argument-type]
            )

    def test_delete(self) -> None:
        owner = _Owner()
        with pytest.raises(NotDeletable):
            _Owner.my_first_prop.delete(owner)

    def test___get____with_class(self) -> None:
        assert isinstance(_Owner.my_first_prop, _Prop)
        assert _Owner.my_first_prop is _Owner.my_first_prop

    def test___get____with_instance(self) -> None:
        value = _Value()

        class _Owner(_PropOwner):
            my_first_prop = _Prop(value)

        owner = _Owner()
        assert owner.my_first_prop == (owner, value)

    def test___set__(self) -> None:
        owner = _Owner()
        with pytest.raises(NotSettable):
            owner.my_first_prop = Never  # ty:ignore[invalid-assignment]

    def test___delete__(self) -> None:
        owner = _Owner()
        with pytest.raises(NotDeletable):
            del owner.my_first_prop

    def test_pre_init_owner(self) -> None:
        assert _Owner.my_first_prop in _Owner().pre_init_properties

    def test_post_init_owner(self) -> None:
        assert _Owner.my_first_prop in _Owner().post_init_properties

    def test_delete_owner(self) -> None:
        owner = _Owner()
        _Owner.my_first_prop.delete_owner(owner)

    def test_ownership(self) -> None:
        assert _Owner.my_first_prop.ownership.owner is _Owner
        assert _Owner.my_first_prop.ownership.name == "my_first_prop"

    def test_is_settable(self) -> None:
        assert not _Owner.my_first_prop.is_settable(_Owner())

    def test_assert_settable__without_settable(self) -> None:
        with pytest.raises(NotSettable):
            _Owner.my_first_prop.assert_settable(_Owner())

    def test_assert_settable__with_settable(self) -> None:
        class _SettableProp(_Prop):
            @override
            def is_settable(self, owner: _PropOwner, /) -> bool:
                return True

        class _SettableOwner(_PropOwner):
            my_first_prop = _SettableProp()

        _SettableOwner.my_first_prop.assert_settable(_SettableOwner())

    def test_is_deletable(self) -> None:
        assert not _Owner.my_first_prop.is_deletable(_Owner())

    def test_assert_deletable__without_deletable(self) -> None:
        with pytest.raises(NotDeletable):
            _Owner.my_first_prop.assert_deletable(_Owner())

    def test_assert_deletable__with_deletable(self) -> None:
        class _DeletableProp(_Prop):
            @override
            def is_deletable(self, owner: _PropOwner, /) -> bool:
                return True

        class _DeletableOwner(_PropOwner):
            my_first_prop = _DeletableProp()

        _DeletableOwner.my_first_prop.assert_deletable(_DeletableOwner())


class TestPropError:
    def test___init__(self) -> None:
        message = "Hello, world!"
        sut = PropError(_Owner.my_first_prop, message)
        assert str(sut) == message
        assert sut.prop is _Owner.my_first_prop


class TestOwnerError:
    def test___init__(self) -> None:
        owner = _Owner()
        message = "Hello, world!"
        sut = OwnerError(_Owner.my_first_prop, owner, message)
        assert str(sut) == message
        assert sut.obj is owner
        assert sut.name == "my_first_prop"


class TestNotSettable:
    def test___init__(self) -> None:
        sut = NotSettable(_Owner.my_first_prop, _Owner())
        assert "my_first_prop" in str(sut)


class TestNotDeletable:
    def test___init__(self) -> None:
        sut = NotDeletable(_Owner.my_first_prop, _Owner())
        assert "my_first_prop" in str(sut)
