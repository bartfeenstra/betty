from __future__ import annotations

from typing_extensions import override

import pytest

from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.locale.localizable import _, Localizable, static
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
            _UnmetRequirement().assert_met()

    async def test_assert_met_should_do_nothing_if_met(self) -> None:
        _MetRequirement().assert_met()

    async def test_localize_with_details(self) -> None:
        class _Requirement(_MetRequirement):
            def details(self) -> Localizable:
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
            _ReduceToRequirementCollectionRequirementCollection(requirement_1),
            requirement_2,
        ).reduce() == _RequirementCollection(requirement_1, requirement_2)


class _RequirementCollection(RequirementCollection):
    @override
    def is_met(self) -> bool:
        return True  # pragma: no cover

    @override
    def summary(self) -> Localizable:
        return static("Lorem ipsum")


class _ReduceToRequirementCollectionRequirementCollection(_RequirementCollection):
    @override
    def reduce(self) -> Requirement | None:
        return _RequirementCollection(*self._requirements)

    @override
    def summary(self) -> Localizable:
        return static("Lorem ipsum")


class _MetRequirement(Requirement):
    @override
    def is_met(self) -> bool:
        return True

    @override
    def summary(self) -> Localizable:
        return static("Lorem ipsum")


class _UnmetRequirement(Requirement):
    @override
    def is_met(self) -> bool:
        return False

    @override
    def summary(self) -> Localizable:
        return static("Lorem ipsum")


class _ReducedToNoneRequirement(_MetRequirement):
    @override
    def reduce(self) -> Requirement | None:
        return None


class _UnreducedRequirement(_MetRequirement):
    pass


class TestAnyRequirement:
    async def test_is_met_with_one_met(self) -> None:
        assert AnyRequirement(
            _UnmetRequirement(), _UnmetRequirement(), _MetRequirement()
        ).is_met()

    async def test_is_met_without_any_met(self) -> None:
        assert not AnyRequirement(
            _UnmetRequirement(), _UnmetRequirement(), _UnmetRequirement()
        ).is_met()

    async def test_summary(self) -> None:
        assert (AnyRequirement().summary()).localize(DEFAULT_LOCALIZER)


class TestAllRequirements:
    async def test_is_met_with_all_but_one_met(self) -> None:
        assert not AllRequirements(
            _MetRequirement(), _MetRequirement(), _UnmetRequirement()
        ).is_met()

    async def test_is_met_with_all_met(self) -> None:
        assert AllRequirements(
            _MetRequirement(), _MetRequirement(), _MetRequirement()
        ).is_met()

    async def test_summary(self) -> None:
        assert (AllRequirements().summary()).localize(DEFAULT_LOCALIZER)


class TestRequirementError:
    def test_requirement(self) -> None:
        requirement = _UnmetRequirement()
        sut = RequirementError(requirement)
        assert sut.requirement() is requirement
