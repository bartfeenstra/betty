from collections.abc import Iterable
from typing import Any, TypeGuard

from pytest_mock import MockerFixture

from betty.association import AssociateResolver, Association
from betty.associations.proxy import ProxyAssociation
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.entity import Entity
from betty.json_schema import Schema
from betty.portable import PortableData
from betty.project import Project
from betty.test_utils.entity import DummyEntityOne


class _Association(Association):
    def __init__(self):
        super().__init__(FieldDefinition(DataDefinition(label="-")), Entity)

    def is_resolver(
        self, value: Any, /
    ) -> TypeGuard[AssociateResolver[Entity, Entity]]:
        raise NotImplementedError

    def resolve(self, project: Project, owner: Entity, /) -> None:
        raise NotImplementedError

    def associate(self, owner: Entity, associate: Entity, /) -> None:
        raise NotImplementedError

    def disassociate(self, owner: Entity, associate: Entity, /) -> None:
        raise NotImplementedError

    def get_associates(self, owner: Entity, /) -> Iterable[Entity]:
        raise NotImplementedError

    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        raise NotImplementedError

    async def dump_linked_data_for(
        self, project: Project, target: Entity, /
    ) -> PortableData:
        raise NotImplementedError

    def get(self, owner: Entity, /) -> Any:
        raise NotImplementedError


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

    async def test_dump_linked_data_for(
        self, isolated_project: Project, mocker: MockerFixture
    ) -> None:
        dumped_linked_data = {}
        proxied = _Association()
        m_proxied_dump_linked_data_for = mocker.patch.object(
            proxied, "dump_linked_data_for"
        )
        m_proxied_dump_linked_data_for.return_value = dumped_linked_data
        sut = ProxyAssociation(proxied=proxied)
        owner = DummyEntityOne()
        assert (
            await sut.dump_linked_data_for(isolated_project, owner)
            is dumped_linked_data
        )
        m_proxied_dump_linked_data_for.assert_awaited_once_with(isolated_project, owner)

    def test_get_associates(self, mocker: MockerFixture) -> None:
        associates = [DummyEntityOne()]
        proxied = _Association()
        m_proxied_get_associates = mocker.patch.object(proxied, "get_associates")
        m_proxied_get_associates.return_value = associates
        sut = ProxyAssociation(proxied=proxied)
        owner = DummyEntityOne()
        assert sut.get_associates(owner) == associates
        m_proxied_get_associates.assert_called_once_with(owner)

    async def test_linked_data_schema_for(
        self, isolated_project: Project, mocker: MockerFixture
    ) -> None:
        linked_data_schema = Schema()
        proxied = _Association()
        m_proxied_linked_data_schema_for = mocker.patch.object(
            proxied, "linked_data_schema_for"
        )
        m_proxied_linked_data_schema_for.return_value = linked_data_schema
        sut = ProxyAssociation(proxied=proxied)
        assert await sut.linked_data_schema_for(isolated_project) is linked_data_schema
        m_proxied_linked_data_schema_for.assert_awaited_once_with(isolated_project)

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
