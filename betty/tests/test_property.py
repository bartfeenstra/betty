from __future__ import annotations

from typing import TYPE_CHECKING, override

from betty.property import HasProperties, Property, ProxyProperty

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


class _Owner(_PropertyOwner):
    my_first_property = _Property(_Value())


class TestHasProperties:
    def test___init__(self) -> None:
        owner = _Owner()
        assert _Owner.my_first_property in owner.init_properties


class TestProperty:
    def test___get____with_class(self) -> None:
        assert isinstance(_Owner.my_first_property, _Property)
        assert _Owner.my_first_property is _Owner.my_first_property

    def test___get____with_instance(self) -> None:
        value = _Value()

        class _Owner(_PropertyOwner):
            my_first_property = _Property(value)

        owner = _Owner()
        assert owner.my_first_property == (owner, value)

    def test_init_property_owner(self) -> None:
        owner = _Owner()
        assert _Owner.my_first_property in owner.init_properties

    def test_property(self) -> None:
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
