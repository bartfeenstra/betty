from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING

from typing_extensions import override

from betty.model import Entity, UserFacingEntity
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
from betty.project import Project
from betty.test_utils.json.linked_data import assert_dumps_linked_data_for
from betty.test_utils.model import DummyEntity

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump
    from betty.app import App
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
        def __init__(
            self,
            associate: "TestUnidirectionalToZeroOrOne._Associate"
            | ToOneResolver["TestUnidirectionalToZeroOrOne._Associate"]
            | None = None,
        ):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToZeroOrOne[
            "TestUnidirectionalToZeroOrOne._Owner",
            "TestUnidirectionalToZeroOrOne._Associate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._Owner",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._Associate",
        )

    class _OwnerEmbedded(DummyEntity):
        def __init__(
            self, associate: "TestUnidirectionalToZeroOrOne._Associate" | None = None
        ):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToZeroOrOne[
            "TestUnidirectionalToZeroOrOne._OwnerEmbedded",
            "TestUnidirectionalToZeroOrOne._Associate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._OwnerEmbedded",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._Associate",
            linked_data_embedded=True,
        )

    class _OwnerWithUserFacingAssociate(DummyEntity):
        def __init__(
            self,
            associate: "TestUnidirectionalToZeroOrOne._UserFacingAssociate"
            | None = None,
        ):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToZeroOrOne[
            "TestUnidirectionalToZeroOrOne._OwnerWithUserFacingAssociate",
            "TestUnidirectionalToZeroOrOne._UserFacingAssociate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._OwnerWithUserFacingAssociate",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._UserFacingAssociate",
        )

    class _Associate(DummyEntity):
        pass

    class _UserFacingAssociate(UserFacingEntity, DummyEntity):
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

    async def test_linked_data_schema_for(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._Owner.associate.linked_data_schema_for(project)

    async def test_linked_data_schema_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._OwnerEmbedded.associate.linked_data_schema_for(project)

    async def test_dump_linked_data_for_with_publishable(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate("my-first-associate")
            target = self._OwnerWithUserFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected = "/user-facing-associate/my-first-associate/index.json"
            assert actual == expected

    async def test_dump_linked_data_for_with_generated_id(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate()
            target = self._OwnerWithUserFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_without_user_facing(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_without_associate(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            target = self._Owner()
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._Associate()
            target = self._OwnerEmbedded(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected: DumpMapping[Dump] = {
                "id": associate.id,
            }
            assert actual == expected

    async def test_dump_linked_data_for_with_embedded_without_associate(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            target = self._OwnerEmbedded()
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None


class TestBidirectionalToZeroOrOne:
    class _Owner(DummyEntity):
        def __init__(
            self,
            associate: "TestBidirectionalToZeroOrOne._Associate"
            | ToZeroOrOneResolver["TestBidirectionalToZeroOrOne._Associate"]
            | None = None,
        ):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._Owner",
            "TestBidirectionalToZeroOrOne._Associate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Owner",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Associate",
            "owner",
        )

    class _OwnerEmbedded(DummyEntity):
        def __init__(
            self,
            associate: "TestBidirectionalToZeroOrOne._Associate" | None = None,
        ):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._OwnerEmbedded",
            "TestBidirectionalToZeroOrOne._Associate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._OwnerEmbedded",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Associate",
            "owner",
            linked_data_embedded=True,
        )

    class _OwnerWithUserFacingAssociate(DummyEntity):
        def __init__(
            self,
            associate: "TestBidirectionalToZeroOrOne._UserFacingAssociate"
            | None = None,
        ):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._OwnerWithUserFacingAssociate",
            "TestBidirectionalToZeroOrOne._UserFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._OwnerWithUserFacingAssociate",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._UserFacingAssociate",
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

    class _UserFacingAssociate(UserFacingEntity, DummyEntity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._UserFacingAssociate",
            "TestBidirectionalToZeroOrOne._OwnerWithUserFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._UserFacingAssociate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._OwnerWithUserFacingAssociate",
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

    async def test_linked_data_schema_for(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._Owner.associate.linked_data_schema_for(project)

    async def test_linked_data_schema_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._OwnerEmbedded.associate.linked_data_schema_for(project)

    async def test_dump_linked_data_for_with_publishable(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate("my-first-associate")
            target = self._OwnerWithUserFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected = "/user-facing-associate/my-first-associate/index.json"
            assert actual == expected

    async def test_dump_linked_data_for_with_generated_id(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate()
            target = self._OwnerWithUserFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_without_user_facing(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_without_associate(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            target = self._Owner()
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._Associate()
            target = self._OwnerEmbedded(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected: DumpMapping[Dump] = {
                "id": associate.id,
                "owner": None,
            }
            assert actual == expected

    async def test_dump_linked_data_for_with_embedded_without_associate(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            target = self._OwnerEmbedded()
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None


class TestUnidirectionalToOne:
    class _Owner(DummyEntity):
        def __init__(
            self,
            associate: "TestUnidirectionalToOne._Associate"
            | ToOneResolver["TestUnidirectionalToOne._Associate"],
        ):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToOne[
            "TestUnidirectionalToOne._Owner", "TestUnidirectionalToOne._Associate"
        ](
            "betty.tests.model.test_association:TestUnidirectionalToOne._Owner",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToOne._Associate",
        )

    class _OwnerEmbedded(DummyEntity):
        def __init__(self, associate: "TestUnidirectionalToOne._Associate"):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToOne[
            "TestUnidirectionalToOne._OwnerEmbedded",
            "TestUnidirectionalToOne._Associate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToOne._OwnerEmbedded",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToOne._Associate",
            linked_data_embedded=True,
        )

    class _OwnerWithUserFacingAssociate(UserFacingEntity, DummyEntity):
        def __init__(self, associate: "TestUnidirectionalToOne._UserFacingAssociate"):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToOne[
            "TestUnidirectionalToOne._OwnerWithUserFacingAssociate",
            "TestUnidirectionalToOne._UserFacingAssociate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToOne._OwnerWithUserFacingAssociate",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToOne._UserFacingAssociate",
        )

    class _Associate(DummyEntity):
        pass

    class _UserFacingAssociate(UserFacingEntity, DummyEntity):
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

    async def test_linked_data_schema_for(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._Owner.associate.linked_data_schema_for(project)

    async def test_linked_data_schema_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._OwnerEmbedded.associate.linked_data_schema_for(project)

    async def test_dump_linked_data_for_with_publishable(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate("my-first-associate")
            target = self._OwnerWithUserFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected = "/user-facing-associate/my-first-associate/index.json"
            assert actual == expected

    async def test_dump_linked_data_for_with_generated_id(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate()
            target = self._OwnerWithUserFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_without_user_facing(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._Associate()
            target = self._OwnerEmbedded(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected: DumpMapping[Dump] = {
                "id": associate.id,
            }
            assert actual == expected


class TestBidirectionalToOne:
    class _Owner(DummyEntity):
        def __init__(
            self,
            associate: "TestBidirectionalToOne._Associate"
            | ToOneResolver["TestBidirectionalToOne._Associate"],
        ):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToOne[
            "TestBidirectionalToOne._Owner", "TestBidirectionalToOne._Associate"
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._Owner",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToOne._Associate",
            "owner",
        )

    class _Associate(DummyEntity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToOne._Associate", "TestBidirectionalToOne._Owner"
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._Associate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToOne._Owner",
            "associate",
        )

    class _OwnerEmbedded(DummyEntity):
        def __init__(self, associate: "TestBidirectionalToOne._AssociateEmbedded"):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToOne[
            "TestBidirectionalToOne._OwnerEmbedded",
            "TestBidirectionalToOne._AssociateEmbedded",
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._OwnerEmbedded",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToOne._AssociateEmbedded",
            "owner",
            linked_data_embedded=True,
        )

    class _AssociateEmbedded(DummyEntity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToOne._AssociateEmbedded",
            "TestBidirectionalToOne._OwnerEmbedded",
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._AssociateEmbedded",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToOne._OwnerEmbedded",
            "associate",
        )

    class _OwnerWithUserFacingAssociate(DummyEntity):
        def __init__(self, associate: "TestBidirectionalToOne._UserFacingAssociate"):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToOne[
            "TestBidirectionalToOne._OwnerWithUserFacingAssociate",
            "TestBidirectionalToOne._UserFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._OwnerWithUserFacingAssociate",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToOne._UserFacingAssociate",
            "owner",
        )

    class _UserFacingAssociate(UserFacingEntity, DummyEntity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToOne._UserFacingAssociate",
            "TestBidirectionalToOne._OwnerWithUserFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._UserFacingAssociate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToOne._OwnerWithUserFacingAssociate",
            "associate",
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

    async def test_linked_data_schema_for(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._Owner.associate.linked_data_schema_for(project)

    async def test_linked_data_schema_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._OwnerEmbedded.associate.linked_data_schema_for(project)

    async def test_dump_linked_data_for_with_publishable(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate("my-first-associate")
            target = self._OwnerWithUserFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected = "/user-facing-associate/my-first-associate/index.json"
            assert actual == expected

    async def test_dump_linked_data_for_with_generated_id(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate()
            target = self._OwnerWithUserFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_without_user_facing(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._AssociateEmbedded()
            target = self._OwnerEmbedded(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected: DumpMapping[Dump] = {
                "id": associate.id,
                "owner": None,
            }
            assert actual == expected


class TestUnidirectionalToMany:
    class _Owner(DummyEntity):
        associates = UnidirectionalToMany[
            "TestUnidirectionalToMany._Owner", "TestUnidirectionalToMany._Associate"
        ](
            "betty.tests.model.test_association:TestUnidirectionalToMany._Owner",
            "associates",
            "betty.tests.model.test_association:TestUnidirectionalToMany._Associate",
        )

    class _OwnerEmbedded(DummyEntity):
        associates = UnidirectionalToMany[
            "TestUnidirectionalToMany._OwnerEmbedded",
            "TestUnidirectionalToMany._Associate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToMany._OwnerEmbedded",
            "associates",
            "betty.tests.model.test_association:TestUnidirectionalToMany._Associate",
            linked_data_embedded=True,
        )

    class _Associate(DummyEntity):
        pass

    class _UserFacingAssociate(UserFacingEntity, _Associate):
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

    async def test_linked_data_schema_for(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._Owner.associates.linked_data_schema_for(project)

    async def test_linked_data_schema_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._OwnerEmbedded.associates.linked_data_schema_for(project)

    async def test_dump_linked_data_for(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            publishable_associate = self._UserFacingAssociate(
                "my-first-user-facing-associate"
            )
            unpublishable_associate_because_generated_id = self._UserFacingAssociate()
            unpublishable_associate_because_not_user_facing = self._Associate(
                "my-first-associate"
            )
            target = self._Owner()
            target.associates = [
                publishable_associate,
                unpublishable_associate_because_generated_id,
                unpublishable_associate_because_not_user_facing,
            ]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = [
                "/user-facing-associate/my-first-user-facing-associate/index.json"
            ]
            assert actual == expected

    async def test_dump_linked_data_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate_one = self._UserFacingAssociate("my-first-publishable-associate")
            associate_two = self._UserFacingAssociate()
            associate_three = self._Associate("my-first-not-user-facing-associate")
            target = self._OwnerEmbedded()
            target.associates = [associate_one, associate_two, associate_three]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = [
                {
                    "@id": "https://example.com/user-facing-associate/my-first-publishable-associate/index.json",
                    "id": associate_one.id,
                },
                {
                    "id": associate_two.id,
                },
                {
                    "id": associate_three.id,
                },
            ]
            assert actual == expected


class TestBidirectionalToMany:
    class _Owner(DummyEntity):
        associates = BidirectionalToMany[
            "TestBidirectionalToMany._Owner", "TestBidirectionalToMany._Associate"
        ](
            "betty.tests.model.test_association:TestBidirectionalToMany._Owner",
            "associates",
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
            "associates",
        )

    class _OwnerEmbedded(DummyEntity):
        associates = BidirectionalToMany[
            "TestBidirectionalToMany._OwnerEmbedded",
            "TestBidirectionalToMany._AssociateEmbedded",
        ](
            "betty.tests.model.test_association:TestBidirectionalToMany._OwnerEmbedded",
            "associates",
            "betty.tests.model.test_association:TestBidirectionalToMany._AssociateEmbedded",
            "owner",
            linked_data_embedded=True,
        )

    class _AssociateEmbedded(DummyEntity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToMany._AssociateEmbedded",
            "TestBidirectionalToMany._OwnerEmbedded",
        ](
            "betty.tests.model.test_association:TestBidirectionalToMany._AssociateEmbedded",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToMany._OwnerEmbedded",
            "associates",
        )

    class _UserFacingAssociateEmbedded(UserFacingEntity, _AssociateEmbedded):
        pass

    class _OwnerWithUserFacingAssociate(DummyEntity):
        associates = BidirectionalToMany[
            "TestBidirectionalToMany._OwnerWithUserFacingAssociate",
            "TestBidirectionalToMany._UserFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToMany._OwnerWithUserFacingAssociate",
            "associates",
            "betty.tests.model.test_association:TestBidirectionalToMany._UserFacingAssociate",
            "owner",
        )

    class _UserFacingAssociate(UserFacingEntity, DummyEntity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToMany._UserFacingAssociate",
            "TestBidirectionalToMany._OwnerWithUserFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToMany._UserFacingAssociate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToMany._OwnerWithUserFacingAssociate",
            "associates",
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

    async def test_linked_data_schema_for(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._Owner.associates.linked_data_schema_for(project)

    async def test_linked_data_schema_for_with_embedded(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            await self._OwnerEmbedded.associates.linked_data_schema_for(project)

    async def test_dump_linked_data_for_with_publishable(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate("my-first-associate")
            target = self._OwnerWithUserFacingAssociate()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = ["/user-facing-associate/my-first-associate/index.json"]
            assert actual == expected

    async def test_dump_linked_data_for_with_generated_id(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociate()
            target = self._OwnerWithUserFacingAssociate()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            assert actual == []

    async def test_dump_linked_data_for_without_user_facing(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            assert actual == []

    async def test_dump_linked_data_for_with_embedded_with_publishable(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociateEmbedded("my-first-associate")
            target = self._OwnerEmbedded()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = [
                {
                    "@id": "https://example.com/user-facing-associate-embedded/my-first-associate/index.json",
                    "id": associate.id,
                    "owner": None,
                }
            ]
            assert actual == expected

    async def test_dump_linked_data_for_with_embedded_with_generated_id(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._UserFacingAssociateEmbedded()
            target = self._OwnerEmbedded()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = [
                {
                    "id": associate.id,
                    "owner": None,
                },
            ]
            assert actual == expected

    async def test_dump_linked_data_for_with_embedded_without_user_facing(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            associate = self._AssociateEmbedded("my-first-associate")
            target = self._OwnerEmbedded()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = [
                {
                    "id": associate.id,
                    "owner": None,
                },
            ]
            assert actual == expected


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
