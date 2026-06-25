from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeGuard
from unittest.mock import MagicMock

import pytest

from betty.association import (
    AssociateResolver,
    Association,
    BiResolver,
    UnresolvedAssociate,
    resolve_associate,
    resolve_associates,
)
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.entity import Entity, EntityDefinition
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE

if TYPE_CHECKING:
    from collections.abc import Iterable

    from pytest_mock import MockerFixture

    from betty.linked_data import LinkedData
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidableType, VoidType


class _Association[OwnerT: Entity = Entity, AssociateT: Entity = Entity](
    Association[OwnerT, AssociateT, AssociateT, AssociateT]
):
    def __init__(
        self,
        associate: type[AssociateT] | str,
        associate_attr: Association[AssociateT, OwnerT, Any, Any] | str | None = None,
        /,
    ):
        super().__init__(
            FieldDefinition(DataDefinition(label="-")), associate, associate_attr
        )

    def is_resolver(
        self, value: Any, /
    ) -> TypeGuard[AssociateResolver[OwnerT, AssociateT]]:
        raise NotImplementedError

    def resolve(self, project: Project, owner: OwnerT, /) -> None:
        raise NotImplementedError

    def associate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        raise NotImplementedError

    def disassociate(self, owner: OwnerT, associate: AssociateT, /) -> None:
        raise NotImplementedError

    def get_associates(self, owner: OwnerT, /) -> Iterable[AssociateT]:
        raise NotImplementedError

    async def schema(self, project: Project, /) -> VoidableType[PortableMapping]:
        raise NotImplementedError

    async def dump(self, project: Project, data: OwnerT, /) -> LinkedData | VoidType:
        raise NotImplementedError

    def get(self, owner: Entity, /) -> AssociateT:
        raise NotImplementedError


@EntityDefinition(
    "named",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _NamedEntity(Entity):
    association = _Association["_NamedEntity", "_TypedEntity"](
        "betty.tests.test_association:_TypedEntity"
    )


@EntityDefinition(
    "typed",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _TypedEntity(Entity):
    association = _Association["_TypedEntity", _NamedEntity](_NamedEntity)


@EntityDefinition(
    "bi-named",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _BiNamedEntity(Entity):
    association = _Association["_BiNamedEntity", "_BiTypedEntity"](
        "betty.tests.test_association:_BiTypedEntity", "association"
    )


@EntityDefinition(
    "bi-typed",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _BiTypedEntity(Entity):
    association = _Association(_BiNamedEntity, _BiNamedEntity.association)


class _AssociateDeclaresBidirectionalityOwner(Entity):
    association = _Association[
        "_AssociateDeclaresBidirectionalityOwner",
        "_AssociateDeclaresBidirectionalityAssociate",
    ]("betty.tests.test_association:_AssociateDeclaresBidirectionalityAssociate")


class _AssociateDeclaresBidirectionalityAssociate(Entity):
    association = _Association(
        _AssociateDeclaresBidirectionalityOwner,
        _AssociateDeclaresBidirectionalityOwner.association,
    )


class TestAssociation:
    def test_associate_attr__without(self) -> None:
        assert _NamedEntity.association.associate_attr is None
        assert _TypedEntity.association.associate_attr is None

    def test_associate_attr__with_attr(self) -> None:
        assert _BiTypedEntity.association.associate_attr is _BiNamedEntity.association

    def test_associate_attr__with_name(self) -> None:
        assert _BiNamedEntity.association.associate_attr is _BiTypedEntity.association

    def test_associate_attr__associate_type_declares_bidirectionality(self) -> None:
        assert (
            _AssociateDeclaresBidirectionalityOwner.association.associate_attr
            is _AssociateDeclaresBidirectionalityAssociate.association
        )

    def test_associate_attr_name__with_attr(self) -> None:
        assert _BiTypedEntity.association.associate_attr_name == "association"

    def test_associate_attr_name__with_name(self) -> None:
        assert _BiNamedEntity.association.associate_attr_name == "association"

    def test_associate_type__with_type(self) -> None:
        assert _TypedEntity.association.associate_type is _NamedEntity
        assert _BiTypedEntity.association.associate_type is _BiNamedEntity

    def test_associate_type__with_name(self) -> None:
        assert _NamedEntity.association.associate_type is _TypedEntity
        assert _BiNamedEntity.association.associate_type is _BiTypedEntity

    def test_assert_not_resolver__without_resolver(self) -> None:
        class IsNoResolverAssociation(_Association):
            def is_resolver(
                self, value: Any, /
            ) -> TypeGuard[AssociateResolver[Entity, Entity]]:
                return False

        @EntityDefinition(
            "named",
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        class _Entity(Entity):
            association = IsNoResolverAssociation(_TypedEntity)

        _Entity.association.assert_not_resolver(_Entity(), _TypedEntity())

    def test_assert_not_resolver__with_resolver(self) -> None:
        class IsResolverAssociation(_Association):
            def is_resolver(
                self, value: Any, /
            ) -> TypeGuard[AssociateResolver[Entity, Entity]]:
                return True

        @EntityDefinition(
            "named",
            label="-",
            label_plural="-",
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        class _Entity(Entity):
            association = IsResolverAssociation(_TypedEntity)

        with pytest.raises(UnresolvedAssociate):
            _Entity.association.assert_not_resolver(_Entity(), _TypedEntity())


def test_resolve_associate__without_arguments(isolated_project: Project) -> None:
    associate = Entity()
    assert (
        resolve_associate(
            isolated_project, Entity(), MagicMock(spec=Association), lambda: associate
        )
        is associate
    )


def test_resolve_associate__with_project(isolated_project: Project) -> None:
    associate = Entity()

    def resolver(resolver_project: Project) -> Entity:
        assert resolver_project is isolated_project
        return associate

    assert (
        resolve_associate(
            isolated_project, Entity(), MagicMock(spec=Association), resolver
        )
        is associate
    )


def test_resolve_associate__with_owner_and_association(
    isolated_project: Project,
) -> None:
    owner = Entity()
    association = MagicMock(spec=Association)
    associate = Entity()

    def resolver(resolver_owner: Entity, resolver_association: Association) -> Entity:
        assert resolver_owner is owner
        assert resolver_association is association
        return associate

    assert (
        resolve_associate(isolated_project, owner, association, resolver) is associate
    )


def test_resolve_associate__with_project_and_owner_and_association(
    isolated_project: Project,
) -> None:
    owner = Entity()
    association = MagicMock(spec=Association)
    associate = Entity()

    def resolver(
        resolver_project: Project,
        resolver_owner: Entity,
        resolver_association: Association,
    ) -> Entity:
        assert resolver_project is isolated_project
        assert resolver_owner is owner
        assert resolver_association is association
        return associate

    assert (
        resolve_associate(isolated_project, owner, association, resolver) is associate
    )


def test_resolve_associates(isolated_project: Project, mocker: MockerFixture) -> None:
    associate = DummyEntityOne()

    @EntityDefinition(
        "-",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Entity(Entity):
        association = mocker.MagicMock(spec=Association)
        association.field = FieldDefinition(DataDefinition(label="-"))
        association.resolve.return_value = associate

    entity = _Entity()
    resolve_associates(isolated_project, entity)
    _Entity.association.resolve.assert_called_once_with(isolated_project, entity)


class TestUnresolvedAssociate:
    def test(self) -> None:
        assert str(
            UnresolvedAssociate(
                _NamedEntity(), _NamedEntity.association, lambda _: _TypedEntity()
            )
        )


class TestBiResolver:
    def test___call__(self, isolated_project: Project, mocker: MockerFixture) -> None:
        owner = _BiNamedEntity()
        associate = _BiTypedEntity()
        sut = BiResolver[_BiNamedEntity, _BiTypedEntity](lambda: associate)
        m_associate = mocker.patch.object(_BiTypedEntity.association, "associate")
        assert sut(isolated_project, owner, _BiNamedEntity.association) is associate
        m_associate.assert_called_once_with(associate, owner)
