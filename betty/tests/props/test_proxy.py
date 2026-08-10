from __future__ import annotations

from typing import TYPE_CHECKING

from betty.prop import HasProps, Prop
from betty.props.proxy import ProxyProp

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestProxyProp:
    def test___set_name__(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Prop)

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        m_proxied.__set_name__.assert_called_once_with(_Owner, "my_first_prop")

    def test_get(self, mocker: MockerFixture) -> None:
        value = "Hello, world!"
        m_proxied = mocker.MagicMock(spec=Prop)
        m_proxied.get.return_value = value

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        owner = _Owner()
        assert owner.my_first_prop == value
        m_proxied.get.assert_called_once_with(owner)

    def test_set(self, mocker: MockerFixture) -> None:
        value = "Hello, world!"
        m_proxied = mocker.MagicMock(spec=Prop)

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        owner = _Owner()
        owner.my_first_prop = value
        m_proxied.set.assert_called_once_with(owner, value)

    def test_delete(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Prop)

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        owner = _Owner()
        del owner.my_first_prop
        m_proxied.delete.assert_called_once_with(owner)

    def test_pre_init_owner(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Prop)

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        owner = _Owner()
        m_proxied.pre_init_owner.assert_called_once_with(owner)

    def test_post_init_owner(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Prop)

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        owner = _Owner()
        m_proxied.post_init_owner.assert_called_once_with(owner)

    def test_delete_owner(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Prop)

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        owner = _Owner()
        _Owner.my_first_prop.delete_owner(owner)
        m_proxied.delete_owner.assert_called_once_with(owner)

    def test_is_settable(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Prop)
        m_proxied.is_settable.return_value = True

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        owner = _Owner()
        assert _Owner.my_first_prop.is_settable(owner)
        m_proxied.is_settable.assert_called_once_with(owner)

    def test_is_deletable(self, mocker: MockerFixture) -> None:
        m_proxied = mocker.MagicMock(spec=Prop)
        m_proxied.is_deletable.return_value = True

        class _Owner(HasProps):
            my_first_prop = ProxyProp(proxied=m_proxied)

        owner = _Owner()
        assert _Owner.my_first_prop.is_deletable(owner)
        m_proxied.is_deletable.assert_called_once_with(owner)
