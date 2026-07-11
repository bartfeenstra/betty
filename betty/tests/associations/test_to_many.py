from __future__ import annotations

from typing import TYPE_CHECKING, Self

import pytest

from betty.associations.to_many import ToMany
from betty.entity import Entity, EntityDefinition
from betty.test_utils.locale.localizable import DUMMY_COUNTABLE_LOCALIZABLE

if TYPE_CHECKING:
    from betty.association import Associate
    from betty.project import Project
    from betty.test_utils.conftest import AssertDumpsLinkedDataFor


@EntityDefinition(
    "owner",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _Owner(Entity):
    associates = ToMany[Self, "_Associate"](
        "betty.tests.associations.test_to_many:_Associate",
        "owners",
        label="-",
    )


@EntityDefinition(
    "associate",
    label="-",
    label_plural="-",
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class _Associate(Entity):
    owners = ToMany[Self, _Owner](_Owner, "associates", label="-")


class TestToMany:
    def test_associate(self) -> None:
        owner = _Owner()
        associate = _Associate()
        _Owner.associates.associate(owner, associate)
        assert associate in owner.associates
        assert owner not in associate.owners

    def test_delete__without_associates(self) -> None:
        owner = _Owner()
        _Owner.associates.delete(owner)

    def test_delete__with_associate(self) -> None:
        owner = _Owner()
        associate = _Associate()
        owner.associates.add(associate)
        _Owner.associates.delete(owner)
        assert not owner.associates
        assert not associate.owners

    def test_disassociate(self) -> None:
        owner = _Owner()
        associate = _Associate()
        owner.associates.add(associate)
        _Owner.associates.disassociate(owner, associate)
        assert associate not in owner.associates
        assert owner in associate.owners

    def test_get(self) -> None:
        owner = _Owner()
        associate = _Associate()
        owner.associates.add(associate)
        assert list(_Owner.associates.get(owner)) == [associate]

    def test_get_associates(self) -> None:
        owner = _Owner()
        associate = _Associate()
        owner.associates.add(associate)
        assert list(_Owner.associates.get_associates(owner)) == [associate]

    def test_init_owner(self) -> None:
        _Owner()

    def test_set(self) -> None:
        owner = _Owner()
        associate = _Associate()
        _Owner.associates.set(owner, [associate])
        assert list(owner.associates) == [associate]

    @pytest.mark.parametrize(
        ("expected", "value"),
        [
            (True, _Associate),
            (True, lambda _: _Associate()),
            (True, lambda _, __: _Associate()),
            (True, lambda _, __, ___: _Associate()),
            (False, _Associate()),
        ],
    )
    def test_is_resolver(
        self, expected: bool, value: Associate[_Owner, _Associate]
    ) -> None:
        assert _Owner.associates.is_resolver(value) is expected

    def test_resolve(self, isolated_project: Project) -> None:
        owner = _Owner()
        associate = _Associate()

        owner.associates = [lambda: associate]
        type(owner).associates.resolve(isolated_project, owner)
        assert associate in owner.associates

    async def test_schema(self, isolated_project: Project) -> None:
        await _Owner.associates.schema(isolated_project)

    async def test_dump_linked_data_for(
        self, assert_dumps_linked_data_for: AssertDumpsLinkedDataFor
    ) -> None:
        associate = _Associate(id="my-first-associate")
        owner = _Owner(id="my-first-owner")
        owner.associates = [associate]
        actual = await assert_dumps_linked_data_for(type(owner).associates, owner)
        expected = ["/associate/my-first-associate/index.json"]
        assert actual == expected
