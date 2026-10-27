from collections.abc import Iterable
from typing import Any, TypeGuard

from pytest_mock import MockerFixture

from betty.association import AssociateResolver, Association, HasAssociations
from betty.associations.proxy import ProxyAssociation
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.entity import Entity
from betty.project import Project
from betty.test_utils.entity import DummyEntityOne
from betty.typing import Unreachable


class _Association(Association):
    def __init__(self):
        super().__init__(FieldDefinition(DataDefinition(label="-")), Entity)

    def is_resolver(self, value: Any, /) -> TypeGuard[AssociateResolver]:
        raise Unreachable

    def resolve(self, project: Project, owner: HasAssociations, /) -> None:
        raise Unreachable

    def associate(self, owner: HasAssociations, associate: Entity, /) -> None:
        raise Unreachable

    def disassociate(self, owner: HasAssociations, associate: Entity, /) -> None:
        raise Unreachable

    def get_associates(self, owner: HasAssociations, /) -> Iterable[Entity]:
        raise Unreachable

    def get(self, owner: HasAssociations, /) -> Any:
        raise Unreachable


class TestProxyAssociation:
    def test_associate(self, mocker: MockerFixture) -> None:
        proxied = _Association()
        m_proxied_associate = mocker.patch.object(proxied, "associate")
        sut = ProxyAssociation(proxied=proxied)
        owner = DummyEntityOne()
        associate = DummyEntityOne()
        sut.associate(owner, associate)
        m_proxied_associate.assert_called_once_with(owner, associate)

    def test_disassociate(self, mocker: MockerFixture) -> None:
        proxied = _Association()
        m_proxied_disassociate = mocker.patch.object(proxied, "disassociate")
        sut = ProxyAssociation(proxied=proxied)
        owner = DummyEntityOne()
        associate = DummyEntityOne()
        sut.disassociate(owner, associate)
        m_proxied_disassociate.assert_called_once_with(owner, associate)

    def test_get_associates(self, mocker: MockerFixture) -> None:
        associates = [DummyEntityOne()]
        proxied = _Association()
        m_proxied_get_associates = mocker.patch.object(proxied, "get_associates")
        m_proxied_get_associates.return_value = associates
        sut = ProxyAssociation(proxied=proxied)
        owner = DummyEntityOne()
        assert sut.get_associates(owner) == associates
        m_proxied_get_associates.assert_called_once_with(owner)

    def test_is_resolver(self, mocker: MockerFixture) -> None:
        proxied = _Association()
        m_proxied_is_resolver = mocker.patch.object(proxied, "is_resolver")
        m_proxied_is_resolver.return_value = True
        sut = ProxyAssociation(proxied=proxied)
        assert sut.is_resolver(DummyEntityOne)
        m_proxied_is_resolver.assert_called_once_with(DummyEntityOne)

    def test_resolve(self, isolated_project: Project, mocker: MockerFixture) -> None:
        proxied = _Association()
        m_proxied_resolve = mocker.patch.object(proxied, "resolve")
        sut = ProxyAssociation(proxied=proxied)
        owner = DummyEntityOne()
        sut.resolve(isolated_project, owner)
        m_proxied_resolve.assert_called_once_with(isolated_project, owner)
