from __future__ import annotations

import pytest

from betty.locale import DEFAULT_LOCALIZER
from betty.locale.localizable import _, Localizable, plain
from betty.requirement import (
    RequirementCollection,
    RequirementError,
    AllRequirements,
    AnyRequirement,
    Requirement,
)


class TestRequirement:
    async def test_assert_met_should_raise_error_if_unmet(self) -> None:
        with pytest.raises(RequirementError):
            await _UnmetRequirement().assert_met()

    async def test_assert_met_should_do_nothing_if_met(self) -> None:
        await _MetRequirement().assert_met()

    async def test_localize_with_details(self) -> None:
        class _Requirement(_MetRequirement):
            async def details(self) -> Localizable:
                return _("Dolor sit amet")

        assert (
            _Requirement().localize(DEFAULT_LOCALIZER)
            == "Lorem ipsum\n-----------\nDolor sit amet"
        )

    async def test_localize_without_details(self) -> None:
        assert _MetRequirement().localize(DEFAULT_LOCALIZER) == "Lorem ipsum"


class TestRequirementCollection:
    async def test___eq___with_incomparable_type(self) -> None:
        assert _RequirementCollection() != 123

    async def test___eq___with_empty_collections(self) -> None:
        assert _RequirementCollection() == _RequirementCollection()

    async def test___eq___with_non_empty_collections(self) -> None:
        requirement_1 = _MetRequirement()
        requirement_2 = _MetRequirement()
        assert _RequirementCollection(
            requirement_1, requirement_2
        ) == _RequirementCollection(requirement_1, requirement_2)

    async def test___add__(self) -> None:
        requirement_1 = _MetRequirement()
        requirement_2 = _MetRequirement()
        sut = _RequirementCollection(requirement_1)
        sut += requirement_2
        assert [requirement_1, requirement_2] == sut._requirements

    async def test_localize_without_requirements(self) -> None:
        assert _RequirementCollection().localize(DEFAULT_LOCALIZER) == "Lorem ipsum"

    async def test_localize_with_requirements(self) -> None:
        assert (
            _RequirementCollection(_MetRequirement()).localize(DEFAULT_LOCALIZER)
            == "Lorem ipsum\n- Lorem ipsum"
        )

    async def test_reduce_without_requirements(self) -> None:
        assert _RequirementCollection().reduce() is None

    async def test_reduce_without_reduced_requirements(self) -> None:
        unreduced_requirement_1 = _UnreducedRequirement()
        unreduced_requirement_2 = _UnreducedRequirement()
        assert _RequirementCollection(
            unreduced_requirement_1, unreduced_requirement_2
        ).reduce() == _RequirementCollection(
            unreduced_requirement_1, unreduced_requirement_2
        )

    async def test_reduce_with_one_reduced_requirement(self) -> None:
        unreduced_requirement = _UnreducedRequirement()
        assert (
            _RequirementCollection(
                _ReducedToNoneRequirement(), unreduced_requirement
            ).reduce()
            == unreduced_requirement
        )

    async def test_reduce_with_all_reduced_requirements(self) -> None:
        assert (
            _RequirementCollection(
                _ReducedToNoneRequirement(), _ReducedToNoneRequirement()
            ).reduce()
            is None
        )

    async def test_reduce_with_reduced_similar_requirement_collection(self) -> None:
        requirement_1 = _MetRequirement()
        requirement_2 = _MetRequirement()
        assert _RequirementCollection(
            _RequirementCollection(requirement_1), requirement_2
        ).reduce() == _RequirementCollection(requirement_1, requirement_2)


class _RequirementCollection(RequirementCollection):
    async def is_met(self) -> bool:
        return True

    async def summary(self) -> Localizable:
        return plain("Lorem ipsum")


class _MetRequirement(Requirement):
    async def is_met(self) -> bool:
        return True

    async def summary(self) -> Localizable:
        return plain("Lorem ipsum")


class _UnmetRequirement(Requirement):
    async def is_met(self) -> bool:
        return False

    async def summary(self) -> Localizable:
        return plain("Lorem ipsum")


class _ReducedToNoneRequirement(_MetRequirement):
    def reduce(self) -> Requirement | None:
        return None


class _UnreducedRequirement(_MetRequirement):
    pass


class TestAnyRequirement:
    async def test_is_met_with_one_met(self) -> None:
        assert await AnyRequirement(
            _UnmetRequirement(), _UnmetRequirement(), _MetRequirement()
        ).is_met()

    async def test_is_met_without_any_met(self) -> None:
        assert not await AnyRequirement(
            _UnmetRequirement(), _UnmetRequirement(), _UnmetRequirement()
        ).is_met()

    async def test_summary(self) -> None:
        assert (await AnyRequirement().summary()).localize(DEFAULT_LOCALIZER)


class TestAllRequirements:
    async def test_is_met_with_all_but_one_met(self) -> None:
        assert not await AllRequirements(
            _MetRequirement(), _MetRequirement(), _UnmetRequirement()
        ).is_met()

    async def test_is_met_with_all_met(self) -> None:
        assert await AllRequirements(
            _MetRequirement(), _MetRequirement(), _MetRequirement()
        ).is_met()

    async def test_summary(self) -> None:
        assert (await AllRequirements().summary()).localize(DEFAULT_LOCALIZER)
