from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from betty.property import (
    HasProperties,
    NotSettable,
    OwnerError,
    Property,
    PropertyError,
    ProxyProperty,
    SettableProperty,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class _PropertyOwner(HasProperties):
    def __init__(self):
        self.init_properties = []
        super().__init__()


class _Value:
    pass


class _Property(Property[_PropertyOwner, tuple[_PropertyOwner, _Value]]):
    def __init__(self, value: _Value, /):
        self.__value = value

    @override
    def get(self, owner: _PropertyOwner, /) -> tuple[_PropertyOwner, _Value]:
        return owner, self.__value

    @override
    def init_property_owner(self, owner: _PropertyOwner, /) -> None:
        owner.init_properties.append(self)


class _SettableProperty(
    _Property,
    SettableProperty[
        _PropertyOwner, tuple[_PropertyOwner, _Value], tuple[_PropertyOwner, _Value]
    ],
):
    pass


class TestHasProperties:
    def test___init__(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _Property(_Value())

        owner = _Owner()
        assert _Owner.my_first_property in owner.init_properties


class TestProperty:
    def test___get____with_class(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _Property(_Value())

        assert isinstance(_Owner.my_first_property, _Property)
        assert _Owner.my_first_property is _Owner.my_first_property

    def test___get____with_instance(self) -> None:
        value = _Value()

        class _Owner(_PropertyOwner):
            my_first_property = _Property(value)

        owner = _Owner()
        assert owner.my_first_property == (owner, value)

    def test_init_property_owner(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _Property(_Value())

        owner = _Owner()
        assert _Owner.my_first_property in owner.init_properties

    def test_property(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _Property(_Value())

        assert _Owner.my_first_property.property.owner is _Owner
        assert _Owner.my_first_property.property.name == "my_first_property"


class TestProxyProperty:
    def test___set_name__(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Property)

        class _Owner(HasProperties):
            my_first_property = ProxyProperty(proxied=m_proxied)

        m_proxied.__set_name__.assert_called_once_with(_Owner, "my_first_property")

    def test_get(self, mocker: MockerFixture) -> None:
        value = "Hello, world!"
        m_proxied = mocker.MagicMock(spec=Property)
        m_proxied.get.return_value = value

        class _Owner(HasProperties):
            my_first_property = ProxyProperty(proxied=m_proxied)

        owner = _Owner()
        assert owner.my_first_property == value
        m_proxied.get.assert_called_once_with(owner)

    def test_init_property_owner(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Property)

        class _Owner(HasProperties):
            my_first_property = ProxyProperty(proxied=m_proxied)

        owner = _Owner()
        m_proxied.init_property_owner.assert_called_once_with(owner)


class TestPropertyError:
    def test___init__(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _Property(_Value())

        message = "Hello, world!"
        sut = PropertyError(_Owner.my_first_property, message)
        assert str(sut) == message
        assert sut.property is _Owner.my_first_property


class TestOwnerError:
    def test___init__(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _Property(_Value())

        owner = _Owner()
        message = "Hello, world!"
        sut = OwnerError(_Owner.my_first_property, owner, message)
        assert str(sut) == message
        assert sut.obj is owner
        assert sut.name == "my_first_property"


class TestSettableProperty:
    def test___set__(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _SettableProperty(_Value())

        owner = _Owner()
        with pytest.raises(NotSettable):
            owner.my_first_property = (owner, _Value())

    def test_set(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _SettableProperty(_Value())

        owner = _Owner()
        with pytest.raises(NotSettable):
            _Owner.my_first_property.set(owner, (owner, _Value()))


class TestNotSettable:
    def test___init__(self) -> None:
        class _Owner(_PropertyOwner):
            my_first_property = _SettableProperty(_Value())

        sut = NotSettable(_Owner.my_first_property, _Owner())
        assert "my_first_property" in str(sut)
