from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import pytest
from typing_extensions import override

from betty.model import Entity, EntityDefinition
from betty.model.association import (
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
from betty.project import Project
from betty.test_utils.json.linked_data import assert_dumps_linked_data_for
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.app import App
    from betty.serde.dump import Dump, DumpMapping


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
    class _OwnerBase(Entity):
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

    class _Associate(Entity):
        pass

    def test_get_all_associations__with_base_class_should_return_base_associations(
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

    def test_get_all_associations__with_concrete_class_should_return_all_associations(
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

    def test_get_association__with_base_class_should_return_base_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._OwnerBase, "base_associate")
        assert actual.owner_type is self._OwnerBase
        assert actual.associate_type is self._Associate

    def test_get_association__with_concrete_class_should_return_base_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._Owner, "base_associate")
        assert actual.owner_type is self._OwnerBase
        assert actual.associate_type is self._Associate

    def test_get_association__with_concrete_class_should_return_concrete_association(
        self,
    ) -> None:
        actual = AssociationRegistry.get_association(self._Owner, "associate")
        assert actual.owner_type is self._Owner
        assert actual.associate_type is self._Associate


class TestUnidirectionalToZeroOrOne:
    @EntityDefinition(
        "owner",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(Entity):
        def __init__(
            self,
            associate: ToZeroOrOneAssociate[
                TestUnidirectionalToZeroOrOne._Associate
            ] = None,
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

    @EntityDefinition(
        "owner-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerEmbedded(Entity):
        def __init__(
            self, associate: TestUnidirectionalToZeroOrOne._Associate | None = None
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

    @EntityDefinition(
        "owner-with-non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerWithNonPublicFacingAssociate(Entity):
        def __init__(
            self,
            associate: TestUnidirectionalToZeroOrOne._NonPublicFacingAssociate
            | None = None,
        ):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToZeroOrOne[
            "TestUnidirectionalToZeroOrOne._OwnerWithNonPublicFacingAssociate",
            "TestUnidirectionalToZeroOrOne._NonPublicFacingAssociate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._OwnerWithNonPublicFacingAssociate",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToZeroOrOne._NonPublicFacingAssociate",
        )

    @EntityDefinition(
        "associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(Entity):
        pass

    @EntityDefinition(
        "non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        public_facing=False,
    )
    class _NonPublicFacingAssociate(Entity):
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

    async def test_linked_data_schema_for(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._Owner.associate.linked_data_schema_for(project)

    async def test_linked_data_schema_for__with_embedded(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._OwnerEmbedded.associate.linked_data_schema_for(project)

    async def test_dump_linked_data_for__with_publishable(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected = "/associate/my-first-associate/index.json"
            assert actual == expected

    async def test_dump_linked_data_for__with_generated_id(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate()
            target = self._OwnerWithNonPublicFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__with_non_public_facing(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate("my-first-associate")
            target = self._OwnerWithNonPublicFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__without_associate(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            target = self._Owner()
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__with_embedded(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate()
            target = self._OwnerEmbedded(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected: DumpMapping[Dump] = {
                "id": associate.id,
            }
            assert actual == expected

    async def test_dump_linked_data_for__with_embedded_without_associate(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            target = self._OwnerEmbedded()
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None


class TestBidirectionalToZeroOrOne:
    @EntityDefinition(
        "owner",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(Entity):
        def __init__(
            self,
            associate: ToZeroOrOneAssociate[
                TestBidirectionalToZeroOrOne._Associate
            ] = None,
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

    @EntityDefinition(
        "owner-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerEmbedded(Entity):
        def __init__(
            self,
            associate: TestBidirectionalToZeroOrOne._Associate | None = None,
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

    @EntityDefinition(
        "owner-with-non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerWithNonPublicFacingAssociate(Entity):
        def __init__(
            self,
            associate: TestBidirectionalToZeroOrOne._NonPublicFacingAssociate
            | None = None,
        ):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._OwnerWithNonPublicFacingAssociate",
            "TestBidirectionalToZeroOrOne._NonPublicFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._OwnerWithNonPublicFacingAssociate",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._NonPublicFacingAssociate",
            "owner",
        )

    @EntityDefinition(
        "associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(Entity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._Associate",
            "TestBidirectionalToZeroOrOne._Owner",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Associate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._Owner",
            "associate",
        )

    @EntityDefinition(
        "non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        public_facing=False,
    )
    class _NonPublicFacingAssociate(Entity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToZeroOrOne._NonPublicFacingAssociate",
            "TestBidirectionalToZeroOrOne._OwnerWithNonPublicFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._NonPublicFacingAssociate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToZeroOrOne._OwnerWithNonPublicFacingAssociate",
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

    async def test_linked_data_schema_for(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._Owner.associate.linked_data_schema_for(project)

    async def test_linked_data_schema_for__with_embedded(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._OwnerEmbedded.associate.linked_data_schema_for(project)

    async def test_dump_linked_data_for__with_publishable(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected = "/associate/my-first-associate/index.json"
            assert actual == expected

    async def test_dump_linked_data_for__with_generated_id(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate()
            target = self._OwnerWithNonPublicFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__with_non_public_facing(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate("my-first-associate")
            target = self._OwnerWithNonPublicFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__without_associate(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            target = self._Owner()
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__with_embedded(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate()
            target = self._OwnerEmbedded(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected: DumpMapping[Dump] = {
                "id": associate.id,
                "owner": None,
            }
            assert actual == expected

    async def test_dump_linked_data_for__with_embedded_without_associate(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            target = self._OwnerEmbedded()
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None


class TestUnidirectionalToOne:
    @EntityDefinition(
        "owner",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(Entity):
        def __init__(
            self, associate: ToOneAssociate[TestUnidirectionalToOne._Associate]
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

    @EntityDefinition(
        "owner-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerEmbedded(Entity):
        def __init__(self, associate: TestUnidirectionalToOne._Associate):
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

    @EntityDefinition(
        "owner-with-non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerWithNonPublicFacingAssociate(Entity):
        def __init__(
            self, associate: TestUnidirectionalToOne._NonPublicFacingAssociate
        ):
            super().__init__()
            self.associate = associate

        associate = UnidirectionalToOne[
            "TestUnidirectionalToOne._OwnerWithNonPublicFacingAssociate",
            "TestUnidirectionalToOne._NonPublicFacingAssociate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToOne._OwnerWithNonPublicFacingAssociate",
            "associate",
            "betty.tests.model.test_association:TestUnidirectionalToOne._NonPublicFacingAssociate",
        )

    @EntityDefinition(
        "associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(Entity):
        pass

    @EntityDefinition(
        "non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        public_facing=False,
    )
    class _NonPublicFacingAssociate(Entity):
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

    async def test_linked_data_schema_for(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._Owner.associate.linked_data_schema_for(project)

    async def test_linked_data_schema_for__with_embedded(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._OwnerEmbedded.associate.linked_data_schema_for(project)

    async def test_dump_linked_data_for__with_publishable(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected = "/associate/my-first-associate/index.json"
            assert actual == expected

    async def test_dump_linked_data_for__with_generated_id(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate()
            target = self._OwnerWithNonPublicFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__with_non_public_facing(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate("my-first-associate")
            target = self._OwnerWithNonPublicFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__with_embedded(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate()
            target = self._OwnerEmbedded(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected: DumpMapping[Dump] = {
                "id": associate.id,
            }
            assert actual == expected


class TestBidirectionalToOne:
    @EntityDefinition(
        "owner",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(Entity):
        def __init__(
            self, associate: ToOneAssociate[TestBidirectionalToOne._Associate]
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

    @EntityDefinition(
        "associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(Entity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToOne._Associate", "TestBidirectionalToOne._Owner"
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._Associate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToOne._Owner",
            "associate",
        )

    @EntityDefinition(
        "owner-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerEmbedded(Entity):
        def __init__(self, associate: TestBidirectionalToOne._AssociateEmbedded):
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

    @EntityDefinition(
        "associate-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _AssociateEmbedded(Entity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToOne._AssociateEmbedded",
            "TestBidirectionalToOne._OwnerEmbedded",
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._AssociateEmbedded",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToOne._OwnerEmbedded",
            "associate",
        )

    @EntityDefinition(
        "owner-with-non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerWithNonPublicFacingAssociate(Entity):
        def __init__(self, associate: TestBidirectionalToOne._NonPublicFacingAssociate):
            super().__init__()
            self.associate = associate

        associate = BidirectionalToOne[
            "TestBidirectionalToOne._OwnerWithNonPublicFacingAssociate",
            "TestBidirectionalToOne._NonPublicFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._OwnerWithNonPublicFacingAssociate",
            "associate",
            "betty.tests.model.test_association:TestBidirectionalToOne._NonPublicFacingAssociate",
            "owner",
        )

    @EntityDefinition(
        "non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        public_facing=False,
    )
    class _NonPublicFacingAssociate(Entity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToOne._NonPublicFacingAssociate",
            "TestBidirectionalToOne._OwnerWithNonPublicFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToOne._NonPublicFacingAssociate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToOne._OwnerWithNonPublicFacingAssociate",
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

    async def test_linked_data_schema_for(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._Owner.associate.linked_data_schema_for(project)

    async def test_linked_data_schema_for__with_embedded(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._OwnerEmbedded.associate.linked_data_schema_for(project)

    async def test_dump_linked_data_for__with_publishable(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected = "/associate/my-first-associate/index.json"
            assert actual == expected

    async def test_dump_linked_data_for__with_generated_id(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate()
            target = self._OwnerWithNonPublicFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__with_non_public_facing(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate("my-first-associate")
            target = self._OwnerWithNonPublicFacingAssociate(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            assert actual is None

    async def test_dump_linked_data_for__with_embedded(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._AssociateEmbedded()
            target = self._OwnerEmbedded(associate)
            actual = await assert_dumps_linked_data_for(type(target).associate, target)
            expected: DumpMapping[Dump] = {
                "id": associate.id,
                "owner": None,
            }
            assert actual == expected


class TestUnidirectionalToManySingleType:
    @EntityDefinition(
        "owner",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(Entity):
        associates = UnidirectionalToManySingleType[
            "TestUnidirectionalToManySingleType._Owner",
            "TestUnidirectionalToManySingleType._Associate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToManySingleType._Owner",
            "associates",
            "betty.tests.model.test_association:TestUnidirectionalToManySingleType._Associate",
        )

    @EntityDefinition(
        "owner-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerEmbedded(Entity):
        associates = UnidirectionalToManySingleType[
            "TestUnidirectionalToManySingleType._OwnerEmbedded",
            "TestUnidirectionalToManySingleType._Associate",
        ](
            "betty.tests.model.test_association:TestUnidirectionalToManySingleType._OwnerEmbedded",
            "associates",
            "betty.tests.model.test_association:TestUnidirectionalToManySingleType._Associate",
            linked_data_embedded=True,
        )

    @EntityDefinition(
        "associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(Entity):
        pass

    @EntityDefinition(
        "non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        public_facing=False,
    )
    class _NonPublicFacingAssociate(_Associate):
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

    async def test_linked_data_schema_for(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._Owner.associates.linked_data_schema_for(project)

    async def test_linked_data_schema_for__with_embedded(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._OwnerEmbedded.associates.linked_data_schema_for(project)

    async def test_dump_linked_data_for(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            publishable_associate = self._NonPublicFacingAssociate(
                "my-first-non-public-facing-associate"
            )
            unpublishable_associate_because_generated_id = self._Associate(
                "my-first-associate"
            )
            unpublishable_associate_because_not_public_facing = (
                self._NonPublicFacingAssociate()
            )
            target = self._Owner()
            target.associates = [
                publishable_associate,
                unpublishable_associate_because_generated_id,
                unpublishable_associate_because_not_public_facing,
            ]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = ["/associate/my-first-associate/index.json"]
            assert actual == expected

    async def test_dump_linked_data_for__with_embedded(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate_one = self._Associate("my-first-publishable-associate")
            associate_two = self._NonPublicFacingAssociate()
            associate_three = self._NonPublicFacingAssociate(
                "my-first-non-public-facing-associate"
            )
            target = self._OwnerEmbedded()
            target.associates = [associate_one, associate_two, associate_three]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = [
                {
                    "@id": "https://example.com/associate/my-first-publishable-associate/index.json",
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


class _TestUnidirectionalToManyMultipleTypesOwner(Entity):
    pass


class _TestUnidirectionalToManyMultipleTypesTargetMixin(Entity):
    owner = UnidirectionalToZeroOrOne[
        "_TestUnidirectionalToManyMultipleTypesTargetMixin",
        _TestUnidirectionalToManyMultipleTypesOwner,
    ](
        f"{__name__}:_TestUnidirectionalToManyMultipleTypesTargetMixin",
        "owner",
        f"{__name__}:{_TestUnidirectionalToManyMultipleTypesOwner.__name__}",
        title="Owner",
    )


@EntityDefinition(
    "one",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _TestUnidirectionalToManyMultipleTypesAssociateOne(
    _TestUnidirectionalToManyMultipleTypesTargetMixin, Entity
):
    pass


@EntityDefinition(
    "two",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _TestUnidirectionalToManyMultipleTypesAssociateTwo(
    _TestUnidirectionalToManyMultipleTypesTargetMixin, Entity
):
    pass


class _TestUnidirectionalToManyMultipleTypesAssociateUnknown(Entity):
    pass


class TestUnidirectionalToManyMultipleTypes:
    async def test_support_multiple_types(self) -> None:
        sut = UnidirectionalToManyMultipleTypes[
            _TestUnidirectionalToManyMultipleTypesOwner,
            _TestUnidirectionalToManyMultipleTypesTargetMixin,
        ](
            f"{_TestUnidirectionalToManyMultipleTypesOwner.__module__}:{_TestUnidirectionalToManyMultipleTypesOwner.__name__}",
            "associates",
            f"{_TestUnidirectionalToManyMultipleTypesTargetMixin.__module__}:{_TestUnidirectionalToManyMultipleTypesTargetMixin.__name__}",
        )

        owner = _TestUnidirectionalToManyMultipleTypesOwner()
        associates = sut.__get__(owner, type(owner))

        associate_one = _TestUnidirectionalToManyMultipleTypesAssociateOne()
        associate_two = _TestUnidirectionalToManyMultipleTypesAssociateTwo()
        associates.add(associate_one, associate_two)
        associates_one = associates[_TestUnidirectionalToManyMultipleTypesAssociateOne]
        assert associate_one in associates_one
        assert associate_two not in associates_one
        associates_two = associates[_TestUnidirectionalToManyMultipleTypesAssociateTwo]
        assert associate_one not in associates_two
        assert associate_two in associates_two


class TestBidirectionalToManySingleType:
    @EntityDefinition(
        "owner",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Owner(Entity):
        associates = BidirectionalToManySingleType[
            "TestBidirectionalToManySingleType._Owner",
            "TestBidirectionalToManySingleType._Associate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._Owner",
            "associates",
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._Associate",
            "owner",
        )

    @EntityDefinition(
        "associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _Associate(Entity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToManySingleType._Associate",
            "TestBidirectionalToManySingleType._Owner",
        ](
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._Associate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._Owner",
            "associates",
        )

    @EntityDefinition(
        "owner-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerEmbedded(Entity):
        associates = BidirectionalToManySingleType[
            "TestBidirectionalToManySingleType._OwnerEmbedded",
            "TestBidirectionalToManySingleType._AssociateEmbedded",
        ](
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._OwnerEmbedded",
            "associates",
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._AssociateEmbedded",
            "owner",
            linked_data_embedded=True,
        )

    @EntityDefinition(
        "associate-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _AssociateEmbedded(Entity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToManySingleType._AssociateEmbedded",
            "TestBidirectionalToManySingleType._OwnerEmbedded",
        ](
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._AssociateEmbedded",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._OwnerEmbedded",
            "associates",
        )

    @EntityDefinition(
        "non-public-facing-associate-embedded",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        public_facing=False,
    )
    class _NonPublicFacingAssociateEmbedded(_AssociateEmbedded):
        pass

    @EntityDefinition(
        "owner-with-non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
    )
    class _OwnerWithNonPublicFacingAssociate(Entity):
        associates = BidirectionalToManySingleType[
            "TestBidirectionalToManySingleType._OwnerWithNonPublicFacingAssociate",
            "TestBidirectionalToManySingleType._NonPublicFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._OwnerWithNonPublicFacingAssociate",
            "associates",
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._NonPublicFacingAssociate",
            "owner",
        )

    @EntityDefinition(
        "non-public-facing-associate",
        label=DUMMY_LOCALIZABLE,
        label_plural=DUMMY_LOCALIZABLE,
        label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        public_facing=False,
    )
    class _NonPublicFacingAssociate(Entity):
        owner = BidirectionalToZeroOrOne[
            "TestBidirectionalToManySingleType._NonPublicFacingAssociate",
            "TestBidirectionalToManySingleType._OwnerWithNonPublicFacingAssociate",
        ](
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._NonPublicFacingAssociate",
            "owner",
            "betty.tests.model.test_association:TestBidirectionalToManySingleType._OwnerWithNonPublicFacingAssociate",
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

    async def test_linked_data_schema_for(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._Owner.associates.linked_data_schema_for(project)

    async def test_linked_data_schema_for__with_embedded(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            await self._OwnerEmbedded.associates.linked_data_schema_for(project)

    async def test_dump_linked_data_for__with_publishable(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate("my-first-associate")
            target = self._Owner()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = ["/associate/my-first-associate/index.json"]
            assert actual == expected

    async def test_dump_linked_data_for__with_generated_id(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._Associate()
            target = self._Owner()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            assert actual == []

    async def test_dump_linked_data_for__with_non_public_facing(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociate("my-first-associate")
            target = self._OwnerWithNonPublicFacingAssociate()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            assert actual == []

    async def test_dump_linked_data_for__with_embedded_with_publishable(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._AssociateEmbedded("my-first-associate")
            target = self._OwnerEmbedded()
            target.associates = [associate]
            actual = await assert_dumps_linked_data_for(type(target).associates, target)
            expected = [
                {
                    "@id": "https://example.com/associate-embedded/my-first-associate/index.json",
                    "id": associate.id,
                    "owner": None,
                }
            ]
            assert actual == expected

    async def test_dump_linked_data_for__with_embedded_with_generated_id(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._AssociateEmbedded()
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

    async def test_dump_linked_data_for__with_embedded_with_non_public_facing(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            associate = self._NonPublicFacingAssociateEmbedded("my-first-associate")
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


class _TestBidirectionalToManyMultipleTypesOwner(Entity):
    pass


class _TestBidirectionalToManyMultipleTypesTargetMixin(Entity):
    owner = BidirectionalToZeroOrOne[
        "_TestBidirectionalToManyMultipleTypesTargetMixin",
        _TestBidirectionalToManyMultipleTypesOwner,
    ](
        f"{__name__}:_TestBidirectionalToManyMultipleTypesTargetMixin",
        "owner",
        f"{__name__}:{_TestBidirectionalToManyMultipleTypesOwner.__name__}",
        "associates",
        title="Owner",
    )


@EntityDefinition(
    "one",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _TestBidirectionalToManyMultipleTypesAssociateOne(
    _TestBidirectionalToManyMultipleTypesTargetMixin, Entity
):
    pass


@EntityDefinition(
    "two",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _TestBidirectionalToManyMultipleTypesAssociateTwo(
    _TestBidirectionalToManyMultipleTypesTargetMixin, Entity
):
    pass


class _TestBidirectionalToManyMultipleTypesAssociateUnknown(Entity):
    pass


class TestBidirectionalToManyMultipleTypes:
    async def test_support_multiple_types(self) -> None:
        sut = BidirectionalToManyMultipleTypes[
            _TestBidirectionalToManyMultipleTypesOwner,
            _TestBidirectionalToManyMultipleTypesTargetMixin,
        ](
            f"{_TestBidirectionalToManyMultipleTypesOwner.__module__}:{_TestBidirectionalToManyMultipleTypesOwner.__name__}",
            "associates",
            f"{_TestBidirectionalToManyMultipleTypesTargetMixin.__module__}:{_TestBidirectionalToManyMultipleTypesTargetMixin.__name__}",
            "owner",
        )

        owner = _TestBidirectionalToManyMultipleTypesOwner()
        associates = sut.__get__(owner, type(owner))

        associate_one = _TestBidirectionalToManyMultipleTypesAssociateOne()
        associate_two = _TestBidirectionalToManyMultipleTypesAssociateTwo()
        associates.add(associate_one, associate_two)
        associates_one = associates[_TestBidirectionalToManyMultipleTypesAssociateOne]
        assert associate_one in associates_one
        assert associate_two not in associates_one
        associates_two = associates[_TestBidirectionalToManyMultipleTypesAssociateTwo]
        assert associate_one not in associates_two
        assert associate_two in associates_two


class TestAssociationRequired:
    class _Owner(Entity):
        associate = UnidirectionalToOne[
            "TestAssociationRequired._Owner", "TestAssociationRequired._Associate"
        ](
            "betty.tests.model.test_association:TestAssociationRequired._Owner",
            "associate",
            "betty.tests.model.test_association:TestAssociationRequired._Associate",
        )

    class _Associate(Entity):
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
