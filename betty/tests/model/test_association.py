from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING

from typing_extensions import override

from betty.model import Entity
from betty.model.association import (
    AssociationRegistry,
    UnidirectionalToMany,
    UnidirectionalToZeroOrOne,
    UnidirectionalToOne,
    AssociationRequired,
    BidirectionalToZeroOrOne,
    BidirectionalToOne,
    BidirectionalToMany,
    ToOneResolver,
    ToZeroOrOneResolver,
    ToManyResolver,
)
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from collections.abc import Iterable


_EntityT = TypeVar("_EntityT", bound=Entity)


class _PassthroughToOneResolver(ToOneResolver[_EntityT]):
    def __init__(self, entity: _EntityT):
        self._entity = entity

    @override
    def resolve(self) -> _EntityT:
        return self._entity


class _PassthroughToZeroOrOneResolver(ToZeroOrOneResolver[_EntityT]):
    def __init__(self, entity: _EntityT | None):
        self._entity = entity

    @override
    def resolve(self) -> _EntityT | None:
        return self._entity


class _PassthroughToManyResolver(ToManyResolver[_EntityT]):
    def __init__(self, *entities: _EntityT):
        self._entities = entities

    @override
    def resolve(self) -> Iterable[_EntityT]:
        return self._entities


class TestAssociationRegistry:
    class _OwnerBase(DummyEntity):
        base_associate = UnidirectionalToZeroOrOne[
            "TestAssociationRegistry._OwnerBase",
            "TestAssociationRegistry._Associate",
        ](
            "betty.tests.model.test_association:TestAssociationRegistry._OwnerBase",
            "base_associate",
            "betty.tests.model.test_association:TestAssociationRegistry._Associate",
        )

    class _Owner(_OwnerBase):
        associate = UnidirectionalToZeroOrOne[
            "TestAssociationRegistry._Owner",
            "TestAssociationRegistry._Associate",
        ](
            "betty.tests.model.test_association:TestAssociationRegistry._Owner",
            "associate",
            "betty.tests.model.test_association:TestAssociationRegistry._Associate",
        )

    class _Associate(DummyEntity):
        pass

    def test_get_all_associations_with_base_class_should_return_base_associations(
        self,
    ) -> None:
        actual = AssociationRegistry.get_all_associations(self._OwnerBase)
        assert len(actual) == 1
        assert (
            len(
                list(
                    filter(
                        lambda association: association.owner_type is self._OwnerBase
                        and association.owner_attr_name == "base_associate"
                        and association.associate_type is self._Associate,
                        actual,
                    )
                )
            )
            == 1
        )

    def test_get_all_associations_with_concrete_class_should_return_all_associations(
        self,
    ) -> None:
        actual = AssociationRegistry.get_all_associations(self._Owner)
        assert len(actual) == 2
        assert (
            len(
                list(
                    filter(
                        lambda association: association.owner_type is self._OwnerBase
                        and association.owner_attr_name == "base_associate"
                        and association.associate_type is self._Associate,
                        actual,
                    )
                )
            )
            == 1
        )
        assert (
            len(
                list(
                    filter(
                        lambda association: association.owner_type is self._Owner
                        and association.owner_attr_name == "associate"
                        and association.associate_type is self._Associate,
                        actual,
                    )
                )
            )
            == 1
        )

    def test_get_association_with_base_class_should_return_base_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._OwnerBase, "base_associate")
        assert actual.owner_type is self._OwnerBase
        assert actual.associate_type is self._Associate

    def test_get_association_with_concrete_class_should_return_base_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._Owner, "base_associate")
        assert actual.owner_type is self._OwnerBase
        assert actual.associate_type is self._Associate

    def test_get_association_with_concrete_class_should_return_concrete_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._Owner, "associate")
        assert actual.owner_type is self._Owner
        assert actual.associate_type is self._Associate


class TestUnidirectionalToZeroOrOne:
    class _Owner(DummyEntity):
        associate = UnidirectionalToZeroOrOne[
            "TestUnidirectionalToZeroOrOne._Owner",
            "TestUnidirectionalToZeroOrOne._Associate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._Owner",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._Associate",
        )

    class _Associate(DummyEntity):
        pass

    def test(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = associate
        assert owner.associate is associate

        owner.associate = None
        assert owner.associate is None

        owner.associate = associate
        del owner.associate
        assert owner.associate is None

    def test_resolve_with_to_zero_or_one_resolver_with_zero(self) -> None:
        owner = self._Owner()

        owner.associate = _PassthroughToZeroOrOneResolver(None)
        type(owner).associate.resolve(owner)
        assert owner.associate is None

    def test_resolve_with_to_zero_or_one_resolver_with_one(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToZeroOrOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate

    def test_resolve_with_to_one_resolver(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate


class TestBidirectionalToZeroOrOne:
    class _Owner(DummyEntity):
        associate = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._Owner",
            "TestBidirectionalToZeroOrOne._Associate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Owner",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Associate",
            "owner",
        )

    class _Associate(DummyEntity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._Associate",
            "TestBidirectionalToZeroOrOne._Owner",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Associate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Owner",
            "associate",
        )

    def test(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = associate
        assert owner.associate is associate
        assert associate.owner is owner

        owner.associate = None
        assert owner.associate is None
        assert associate.owner is None

        owner.associate = associate  # type: ignore[unreachable]
        del owner.associate
        assert owner.associate is None
        assert associate.owner is None

    def test_resolve_with_to_zero_or_one_resolver_with_zero(self) -> None:
        owner = self._Owner()

        owner.associate = _PassthroughToZeroOrOneResolver(None)
        type(owner).associate.resolve(owner)
        assert owner.associate is None

    def test_resolve_with_to_zero_or_one_resolver_with_one(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToZeroOrOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate
        assert associate.owner is owner

    def test_resolve_with_to_one_resolver(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate
        assert associate.owner is owner


class TestUnidirectionalToOne:
    class _Owner(DummyEntity):
        associate = UnidirectionalToOne[
            "TestUnidirectionalToOne._Owner", "TestUnidirectionalToOne._Associate"
        ](
            "betty.tests.model.test_association:TestUnidirectionalToOne._Owner",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToOne._Associate",
        )

    class _Associate(DummyEntity):
        pass

    def test(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = associate
        assert owner.associate is associate

    def test_resolve(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate


class TestBidirectionalToOne:
    class _Owner(DummyEntity):
        associate = BidirectionalToOne[
            "TestBidirectionalToOne._Owner", "TestBidirectionalToOne._Associate"
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._Owner",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToOne._Associate",
            "owner",
        )

    class _Associate(DummyEntity):
        owner = BidirectionalToMany[
            "TestBidirectionalToOne._Associate", "TestBidirectionalToOne._Owner"
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._Associate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToOne._Owner",
            "associate",
        )

    def test(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = associate
        assert owner.associate is associate
        assert list(associate.owner) == [owner]

    def test_resolve(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate
        assert owner in associate.owner


class TestUnidirectionalToMany:
    class _Owner(DummyEntity):
        associate = UnidirectionalToMany[
            "TestUnidirectionalToMany._Owner", "TestUnidirectionalToMany._Associate"
        ](
            "betty.tests.model.test_association:TestUnidirectionalToMany._Owner",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToMany._Associate",
        )

    class _Associate(DummyEntity):
        pass

    def test(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = [associate]
        assert list(owner.associate) == [associate]

        del owner.associate
        assert list(owner.associate) == []

    def test_resolve(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToManyResolver(associate)
        type(owner).associate.resolve(owner)
        assert associate in owner.associate


class TestBidirectionalToMany:
    class _Owner(DummyEntity):
        associate = BidirectionalToMany[
            "TestBidirectionalToMany._Owner", "TestBidirectionalToMany._Associate"
        ](
            "betty.tests.model.test_association:TestBidirectionalToMany._Owner",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToMany._Associate",
            "owner",
        )

    class _Associate(DummyEntity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToMany._Associate", "TestBidirectionalToMany._Owner"
        ](
            "betty.tests.model.test_association:TestBidirectionalToMany._Associate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToMany._Owner",
            "associate",
        )

    def test(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = [associate]
        assert list(owner.associate) == [associate]
        assert associate.owner is owner

        del owner.associate
        assert list(owner.associate) == []
        assert associate.owner is None

    def test_resolve(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToManyResolver(associate)
        type(owner).associate.resolve(owner)
        assert associate in owner.associate
        assert associate.owner is owner


class TestAssociationRequired:
    class _Owner(DummyEntity):
        associate = UnidirectionalToOne[
            "TestAssociationRequired._Owner", "TestAssociationRequired._Associate"
        ](
            "betty.tests.model.test_association:TestAssociationRequired._Owner",
            "associate",
            "betty.tests.model.test_association:TestAssociationRequired._Associate",
        )

    class _Associate(DummyEntity):
        pass

    def test_new(self) -> None:
        association = self._Owner.associate
        owner = self._Owner()
        AssociationRequired.new(association, owner)
