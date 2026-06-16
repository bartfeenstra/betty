from __future__ import annotations

from typing import TYPE_CHECKING, Self, override

import pytest

from betty.entity import Entity, EntityDefinition
from betty.entity.association import (
    AssociationRegistry,
    AssociationRequired,
    BidirectionalToManyMultipleTypes,
    BidirectionalToManySingleType,
    BidirectionalToOne,
    BidirectionalToZeroOrOne,
    TemporaryToManyResolver,
    TemporaryToOneResolver,
    TemporaryToZeroOrOneResolver,
    ToManyResolver,
    ToOneAssociate,
    ToOneResolver,
    ToZeroOrOneAssociate,
    ToZeroOrOneResolver,
    UnidirectionalToManyMultipleTypes,
    UnidirectionalToManySingleType,
    UnidirectionalToOne,
    UnidirectionalToZeroOrOne,
)
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.project import Project
    from betty.test_utils.conftest import AssertDumpsLinkedDataFor


class _OwnerBase(Entity):
    def __init__(self):
        super().__init__(id="my-first-owner")


class _AssociateBase(Entity):
    def __init__(self):
        super().__init__(id="my-first-associate")


class _PassthroughToOneResolver[EntityT: Entity](ToOneResolver[EntityT]):
    def __init__(self, entity: EntityT):
        self._entity = entity

    @override
    def resolve(self) -> EntityT:
        return self._entity


class _PassthroughToZeroOrOneResolver[EntityT: Entity](ToZeroOrOneResolver[EntityT]):
    def __init__(self, entity: EntityT | None):
        self._entity = entity

    @override
    def resolve(self) -> EntityT | None:
        return self._entity


class _PassthroughToManyResolver[EntityT: Entity](ToManyResolver[EntityT]):
    def __init__(self, *entities: EntityT):
        self._entities = entities

    @override
    def resolve(self) -> Iterable[EntityT]:
        return self._entities


class TestAssociationRegistry:
    class _OwnerSuper(_OwnerBase):
        base_associate = UnidirectionalToZeroOrOne[
            Self, "TestAssociationRegistry._Associate"
        ](
            "betty.tests.entity.test_association:TestAssociationRegistry._Associate",
            label="-",
        )

    class _OwnerSub(_OwnerSuper):
        associate = UnidirectionalToZeroOrOne[
            Self, "TestAssociationRegistry._Associate"
        ](
            "betty.tests.entity.test_association:TestAssociationRegistry._Associate",
            label="-",
        )

    class _Associate(_AssociateBase):
        pass

    def test_get_all_associations__with_super_class_should_return_base_associations(
        self,
    ) -> None:
        actual = AssociationRegistry.get_all_associations(self._OwnerSuper)
        assert len(actual) == 1
        assert (
            len(
                list(
                    filter(
                        lambda association: (
                            association.owner_type is self._OwnerSuper
                            and association.owner_attr_name == "base_associate"
                            and association.associate_type is self._Associate
                        ),
                        actual,
                    )
                )
            )
            == 1
        )

    def test_get_all_associations__with_concrete_class_should_return_all_associations(
        self,
    ) -> None:
        actual = AssociationRegistry.get_all_associations(self._OwnerSub)
        assert len(actual) == 2
        assert (
            len(
                list(
                    filter(
                        lambda association: (
                            association.owner_type is self._OwnerSuper
                            and association.owner_attr_name == "base_associate"
                            and association.associate_type is self._Associate
                        ),
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
                        lambda association: (
                            association.owner_type is self._OwnerSub
                            and association.owner_attr_name == "associate"
                            and association.associate_type is self._Associate
                        ),
                        actual,
                    )
                )
            )
            == 1
        )

    def test_get_association__with_base_class_should_return_base_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._OwnerSuper, "base_associate")
        assert actual.owner_type is self._OwnerSuper
        assert actual.associate_type is self._Associate

    def test_get_association__with_concrete_class_should_return_base_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._OwnerSub, "base_associate")
        assert actual.owner_type is self._OwnerSuper
        assert actual.associate_type is self._Associate

    def test_get_association__with_concrete_class_should_return_concrete_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._OwnerSub, "associate")
        assert actual.owner_type is self._OwnerSub
        assert actual.associate_type is self._Associate


class TestUnidirectionalToZeroOrOne:
    @EntityDefinition(
        "owner",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(_OwnerBase):
        def __init__(
            self,
            associate: ToZeroOrOneAssociate[
                TestUnidirectionalToZeroOrOne._Associate
            ] = None,
        ):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToZeroOrOne[
            Self, "TestUnidirectionalToZeroOrOne._Associate"
        ](
            "betty.tests.entity.test_association:TestUnidirectionalToZeroOrOne._Associate",
            label="-",
        )

    @EntityDefinition(
        "associate",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(_AssociateBase):
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

    def test_resolve__with_to_zero_or_one_resolver_with_zero(self) -> None:
        owner = self._Owner()

        owner.associate = _PassthroughToZeroOrOneResolver(None)
        type(owner).associate.resolve(owner)
        assert owner.associate is None

    def test_resolve__with_to_zero_or_one_resolver_with_one(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToZeroOrOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate

    def test_resolve__with_to_one_resolver(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate

    async def test_linked_data_schema_for(self, isolated_project: Project) -> None:
        await self._Owner.associate.linked_data_schema_for(isolated_project)

    async def test_dump_linked_data_for(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        associate = self._Associate()
        target = self._Owner(associate)
        actual = await assert_dumps_linked_data_for(type(target).associate, target)
        expected = "/associate/my-first-associate/index.json"
        assert actual == expected

    async def test_dump_linked_data_for__without_associate(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        target = self._Owner()
        actual = await assert_dumps_linked_data_for(type(target).associate, target)
        assert actual is None


class TestBidirectionalToZeroOrOne:
    @EntityDefinition(
        "owner",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(_OwnerBase):
        def __init__(
            self,
            associate: ToZeroOrOneAssociate[
                TestBidirectionalToZeroOrOne._Associate
            ] = None,
        ):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToZeroOrOne[
            Self, "TestBidirectionalToZeroOrOne._Associate"
        ](
            "betty.tests.entity.test_association:TestBidirectionalToZeroOrOne._Associate",
            "owner",
            label="-",
        )

    @EntityDefinition(
        "associate",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(_AssociateBase):
        owner = BidirectionalToZeroOrOne[Self, "TestBidirectionalToZeroOrOne._Owner"](
            "betty.tests.entity.test_association:TestBidirectionalToZeroOrOne._Owner",
            "associate",
            label="-",
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

        owner.associate = associate
        del owner.associate
        assert owner.associate is None
        assert associate.owner is None

    def test_resolve__with_to_zero_or_one_resolver_with_zero(self) -> None:
        owner = self._Owner()

        owner.associate = _PassthroughToZeroOrOneResolver(None)
        type(owner).associate.resolve(owner)
        assert owner.associate is None

    def test_resolve__with_to_zero_or_one_resolver_with_one(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToZeroOrOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate
        assert associate.owner is owner

    def test_resolve__with_to_one_resolver(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associate = _PassthroughToOneResolver(associate)
        type(owner).associate.resolve(owner)
        assert owner.associate is associate
        assert associate.owner is owner

    async def test_linked_data_schema_for(self, isolated_project: Project) -> None:
        await self._Owner.associate.linked_data_schema_for(isolated_project)

    async def test_dump_linked_data_for(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        associate = self._Associate()
        target = self._Owner(associate)
        actual = await assert_dumps_linked_data_for(type(target).associate, target)
        expected = "/associate/my-first-associate/index.json"
        assert actual == expected

    async def test_dump_linked_data_for__without_associate(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        target = self._Owner()
        actual = await assert_dumps_linked_data_for(type(target).associate, target)
        assert actual is None


class TestUnidirectionalToOne:
    @EntityDefinition(
        "owner",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(_OwnerBase):
        def __init__(
            self, associate: ToOneAssociate[TestUnidirectionalToOne._Associate]
        ):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToOne[Self, "TestUnidirectionalToOne._Associate"](
            "betty.tests.entity.test_association:TestUnidirectionalToOne._Associate",
            label="-",
        )

    @EntityDefinition(
        "associate",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(_AssociateBase):
        pass

    def test(self) -> None:
        associate = self._Associate()
        owner = self._Owner(associate)

        owner.associate = associate
        assert owner.associate is associate

    def test_resolve(self) -> None:
        associate = self._Associate()
        owner = self._Owner(_PassthroughToOneResolver(associate))

        type(owner).associate.resolve(owner)
        assert owner.associate is associate

    async def test_linked_data_schema_for(self, isolated_project: Project) -> None:
        await self._Owner.associate.linked_data_schema_for(isolated_project)

    async def test_dump_linked_data_for(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        associate = self._Associate()
        target = self._Owner(associate)
        actual = await assert_dumps_linked_data_for(type(target).associate, target)
        expected = "/associate/my-first-associate/index.json"
        assert actual == expected


class TestBidirectionalToOne:
    @EntityDefinition(
        "owner",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(_OwnerBase):
        def __init__(
            self, associate: ToOneAssociate[TestBidirectionalToOne._Associate]
        ):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToOne[Self, "TestBidirectionalToOne._Associate"](
            "betty.tests.entity.test_association:TestBidirectionalToOne._Associate",
            "owner",
            label="-",
        )

    @EntityDefinition(
        "associate",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(_AssociateBase):
        owner = BidirectionalToZeroOrOne[Self, "TestBidirectionalToOne._Owner"](
            "betty.tests.entity.test_association:TestBidirectionalToOne._Owner",
            "associate",
            label="-",
        )

    def test(self) -> None:
        associate = self._Associate()
        owner = self._Owner(associate)

        assert owner.associate is associate
        assert associate.owner is owner

    def test_resolve(self) -> None:
        associate = self._Associate()
        owner = self._Owner(_PassthroughToOneResolver(associate))

        type(owner).associate.resolve(owner)
        assert owner.associate is associate
        assert associate.owner is owner

    async def test_linked_data_schema_for(self, isolated_project: Project) -> None:
        await self._Owner.associate.linked_data_schema_for(isolated_project)

    async def test_dump_linked_data_for(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        associate = self._Associate()
        target = self._Owner(associate)
        actual = await assert_dumps_linked_data_for(type(target).associate, target)
        expected = "/associate/my-first-associate/index.json"
        assert actual == expected


class TestUnidirectionalToManySingleType:
    @EntityDefinition(
        "owner",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(_OwnerBase):
        associates = UnidirectionalToManySingleType[
            Self, "TestUnidirectionalToManySingleType._Associate"
        ](
            "betty.tests.entity.test_association:TestUnidirectionalToManySingleType._Associate",
            label="-",
        )

    @EntityDefinition(
        "associate",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(_AssociateBase):
        pass

    def test(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associates = [associate]
        assert list(owner.associates) == [associate]

        del owner.associates
        assert list(owner.associates) == []

    def test_resolve(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associates = _PassthroughToManyResolver(associate)
        type(owner).associates.resolve(owner)
        assert associate in owner.associates

    async def test_linked_data_schema_for(self, isolated_project: Project) -> None:
        await self._Owner.associates.linked_data_schema_for(isolated_project)

    async def test_dump_linked_data_for(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        associate = self._Associate()
        target = self._Owner()
        target.associates = [associate]
        actual = await assert_dumps_linked_data_for(type(target).associates, target)
        expected = ["/associate/my-first-associate/index.json"]
        assert actual == expected


class TestUnidirectionalToManyMultipleTypes:
    class _Owner(_OwnerBase):
        associates = UnidirectionalToManyMultipleTypes[
            Self, "TestUnidirectionalToManyMultipleTypes._TargetMixin"
        ](
            "betty.tests.entity.test_association:TestUnidirectionalToManyMultipleTypes._TargetMixin",
            label="-",
        )

    class _TargetMixin(Entity):
        owner = UnidirectionalToZeroOrOne[
            Self, "TestUnidirectionalToManyMultipleTypes._Owner"
        ](
            "betty.tests.entity.test_association:TestUnidirectionalToManyMultipleTypes._Owner",
            label="Owner",
        )

    @EntityDefinition(
        "one",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _AssociateOne(_TargetMixin):
        pass

    @EntityDefinition(
        "two",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _AssociateTwo(_TargetMixin):
        pass

    async def test_support_multiple_types(self) -> None:
        owner = self._Owner()

        associate_one = self._AssociateOne()
        associate_two = self._AssociateTwo()
        owner.associates.add(associate_one, associate_two)
        associates_one = owner.associates[self._AssociateOne]
        assert associate_one in associates_one
        assert associate_two not in associates_one
        associates_two = owner.associates[self._AssociateTwo]
        assert associate_one not in associates_two
        assert associate_two in associates_two


class TestBidirectionalToManySingleType:
    @EntityDefinition(
        "owner",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(_OwnerBase):
        associates = BidirectionalToManySingleType[
            Self, "TestBidirectionalToManySingleType._Associate"
        ](
            "betty.tests.entity.test_association:TestBidirectionalToManySingleType._Associate",
            "owner",
            label="-",
        )

    @EntityDefinition(
        "associate",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(_AssociateBase):
        owner = BidirectionalToZeroOrOne[
            Self, "TestBidirectionalToManySingleType._Owner"
        ](
            "betty.tests.entity.test_association:TestBidirectionalToManySingleType._Owner",
            "associates",
            label="-",
        )

    def test(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associates = [associate]
        assert list(owner.associates) == [associate]
        assert associate.owner is owner

        del owner.associates
        assert list(owner.associates) == []
        assert associate.owner is None

    def test_resolve(self) -> None:
        owner = self._Owner()
        associate = self._Associate()

        owner.associates = _PassthroughToManyResolver(associate)
        type(owner).associates.resolve(owner)
        assert associate in owner.associates
        assert associate.owner is owner

    async def test_linked_data_schema_for(self, isolated_project: Project) -> None:
        await self._Owner.associates.linked_data_schema_for(isolated_project)

    async def test_dump_linked_data_for(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        associate = self._Associate()
        target = self._Owner()
        target.associates = [associate]
        actual = await assert_dumps_linked_data_for(type(target).associates, target)
        expected = ["/associate/my-first-associate/index.json"]
        assert actual == expected


class TestBidirectionalToManyMultipleTypes:
    class _Owner(_OwnerBase):
        associates = BidirectionalToManyMultipleTypes[
            Self, "TestBidirectionalToManyMultipleTypes._TargetMixin"
        ](
            "betty.tests.entity.test_association:TestBidirectionalToManyMultipleTypes._TargetMixin",
            "owner",
            label="-",
        )

    class _TargetMixin(Entity):
        owner = BidirectionalToZeroOrOne[
            Self, "TestBidirectionalToManyMultipleTypes._Owner"
        ](
            "betty.tests.entity.test_association:TestBidirectionalToManyMultipleTypes._Owner",
            "associates",
            label="Owner",
        )

    @EntityDefinition(
        "one",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _AssociateOne(_TargetMixin):
        pass

    @EntityDefinition(
        "two",
        label="-",
        label_plural="-",
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _AssociateTwo(_TargetMixin):
        pass

    def test_support_multiple_types(self) -> None:
        owner = self._Owner()

        associate_one = self._AssociateOne()
        associate_two = self._AssociateTwo()
        owner.associates.add(associate_one, associate_two)
        associates_one = owner.associates[self._AssociateOne]
        assert associate_one in associates_one
        assert associate_two not in associates_one
        associates_two = owner.associates[self._AssociateTwo]
        assert associate_one not in associates_two
        assert associate_two in associates_two


class TestAssociationRequired:
    class _Owner(_OwnerBase):
        associate = UnidirectionalToOne[Self, "TestAssociationRequired._Associate"](
            "betty.tests.entity.test_association:TestAssociationRequired._Associate",
            label="-",
        )

    class _Associate(_AssociateBase):
        pass

    def test_new(self) -> None:
        association = self._Owner.associate
        owner = self._Owner()
        AssociationRequired(association, owner)


class TestTemporaryToZeroOrOneResolver:
    def test_resolve(self) -> None:
        sut = TemporaryToZeroOrOneResolver[Entity]()
        with pytest.raises(RuntimeError):
            sut.resolve()


class TestTemporaryToOneResolver:
    def test_resolve(self) -> None:
        sut = TemporaryToOneResolver[Entity]()
        with pytest.raises(RuntimeError):
            sut.resolve()


class TestTemporaryToManyResolver:
    def test_resolve(self) -> None:
        sut = TemporaryToManyResolver[Entity]()
        with pytest.raises(RuntimeError):
            sut.resolve()
