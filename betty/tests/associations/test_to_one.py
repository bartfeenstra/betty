from __future__ import annotations

from typing import TYPE_CHECKING, Self

import pytest

from betty.associations.to_one import (
    MissingAssociate,
    Placeholder,
    ToOne,
    ToOneAssociate,
)
from betty.entity import Entity, EntityDefinition
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE

if TYPE_CHECKING:
    from betty.project import Project
    from betty.test_utils.conftest import AssertDumpsLinkedDataFor


@EntityDefinition(
    "owner",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _Owner(Entity):
    associate = ToOne[Self, "_Associate"](
        "betty.tests.associations.test_to_one:_Associate", label="-"
    )


@EntityDefinition(
    "associate",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _Associate(Entity):
    owner = ToOne[Self, _Owner](_Owner, label="-")


@EntityDefinition(
    "bi-owner",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _BiOwner(Entity):
    associate = ToOne[Self, "_BiAssociate"](
        "betty.tests.associations.test_to_one:_BiAssociate",
        "owner",
        label="-",
    )


@EntityDefinition(
    "bi-associate",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _BiAssociate(Entity):
    owner = ToOne[Self, _BiOwner](_BiOwner, "associate", label="-")


class TestToOne:
    def test_associate(self) -> None:
        owner = _BiOwner()
        associate = _BiAssociate()
        _BiOwner.associate.associate(owner, associate)
        assert owner.associate is associate
        with pytest.raises(MissingAssociate):
            assert associate.owner

    def test_init_owner(self) -> None:
        _Owner()

    def test_delete_owner__without_bidirectional_without_entity(self) -> None:
        owner = _Owner()
        _Owner.associate.delete_owner(owner)
        with pytest.raises(MissingAssociate):
            assert owner.associate

    def test_delete_owner__with_bidirectional_without_entity(self) -> None:
        owner = _BiOwner()
        _BiOwner.associate.delete_owner(owner)
        with pytest.raises(MissingAssociate):
            assert owner.associate

    def test_delete_owner__without_bidirectional_with_entity(self) -> None:
        owner = _Owner()
        owner.associate = _Associate()
        _Owner.associate.delete_owner(owner)
        with pytest.raises(MissingAssociate):
            assert owner.associate

    def test_delete_owner__with_bidirectional_with_entity(self) -> None:
        owner = _BiOwner()
        owner.associate = _BiAssociate()
        _BiOwner.associate.delete_owner(owner)
        with pytest.raises(MissingAssociate):
            assert owner.associate

    def test_disassociate(self) -> None:
        associate = _BiAssociate()
        owner = _BiOwner()
        owner.associate = associate
        _BiOwner.associate.disassociate(owner, associate)
        with pytest.raises(MissingAssociate):
            assert owner.associate
        assert associate.owner is owner

    def test_get(self) -> None:
        associate = _BiAssociate()
        owner = _BiOwner()
        owner.associate = associate
        assert _BiOwner.associate.get(owner) is associate

    def test_get_associates(self) -> None:
        associate = _BiAssociate()
        owner = _BiOwner()
        owner.associate = associate
        assert list(_BiOwner.associate.get_associates(owner)) == [associate]

    def test_optional(self) -> None:
        assert ToOne(_BiAssociate, label="-").optional

    def test_set__without_bidirectional(self) -> None:
        owner = _Owner()
        owner.associate = _Associate()
        associate = _Associate()
        _Owner.associate.set(owner, associate)
        assert owner.associate is associate
        with pytest.raises(MissingAssociate):
            assert associate.owner

    def test_set__with_bidirectional(self) -> None:
        owner = _BiOwner()
        associate = _BiAssociate()
        _BiOwner.associate.set(owner, associate)
        assert owner.associate is associate
        assert associate.owner is owner

    @pytest.mark.parametrize(
        ("expected", "value"),
        [
            (True, _BiAssociate),
            (True, lambda _: _BiAssociate()),
            (True, lambda _, __: _BiAssociate()),
            (True, lambda _, __, ___: _BiAssociate()),
            (False, _BiAssociate()),
            (False, Placeholder()),
        ],
    )
    def test_is_resolver(
        self, expected: bool, value: ToOneAssociate[_BiOwner, _BiAssociate]
    ) -> None:
        assert _BiOwner.associate.is_resolver(value) is expected

    def test_resolve(self, isolated_project: Project) -> None:
        associate = _BiAssociate()
        owner = _BiOwner()
        owner.associate = lambda: associate

        type(owner).associate.resolve(isolated_project, owner)
        assert owner.associate is associate

    async def test_linked_data_schema_for(self, isolated_project: Project) -> None:
        await _BiOwner.associate.linked_data_schema_for(isolated_project)

    async def test_dump_linked_data_for(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        associate = _Associate(id="my-first-associate")
        owner = _Owner(id="my-first-owner")
        owner.associate = associate
        actual = await assert_dumps_linked_data_for(type(owner).associate, owner)
        expected = "/associate/my-first-associate/index.json"
        assert actual == expected
