from __future__ import annotations

import pytest
from typing_extensions import override

from betty.locale.localizable import Localizable, Plain, _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.requirement import (
    AllRequirements,
    AnyRequirement,
    Requirement,
    RequirementCollection,
    RequirementError,
    StaticRequirement,
)


class TestRequirement:
    async def test_assert_met__should_raise_error_if_unmet(self) -> None:
        with pytest.raises(RequirementError):
            _UnmetRequirement().assert_met()

    async def test_assert_met__should_do_nothing_if_met(self) -> None:
        _MetRequirement().assert_met()

    async def test_localize__with_details(self) -> None:
        class _Requirement(_MetRequirement):
            @override
            def details(self) -> Localizable:
                return _("Dolor sit amet")

        assert (
            _Requirement().localize(DEFAULT_LOCALIZER)
            == "_Requirement\n------------\nDolor sit amet"
        )

    async def test_localize__without_details(self) -> None:
        assert _MetRequirement().localize(DEFAULT_LOCALIZER) == "_MetRequirement"


class TestRequirementCollection:
    async def test___eq____with_incomparable_type(self) -> None:
        assert _RequirementCollection() != 123

    async def test___eq____with_empty_collections(self) -> None:
        assert _RequirementCollection() == _RequirementCollection()

    async def test___eq____with_non_empty_collections(self) -> None:
        requirement_1 = _MetRequirement()
        requirement_2 = _MetRequirement()
        assert _RequirementCollection(
            requirement_1, requirement_2
        ) == _RequirementCollection(requirement_1, requirement_2)

    async def test_localize__without_requirements(self) -> None:
        assert (
            _RequirementCollection().localize(DEFAULT_LOCALIZER)
            == "_RequirementCollection"
        )

    async def test_localize__with_requirements(self) -> None:
        assert (
            _RequirementCollection(_MetRequirement()).localize(DEFAULT_LOCALIZER)
            == "_RequirementCollection\n\n- _MetRequirement"
        )

    async def test_reduce__without_requirements(self) -> None:
        assert _RequirementCollection().reduce() is None

    async def test_reduce__without_reduced_requirements(self) -> None:
        unreduced_requirement_1 = _UnreducedRequirement()
        unreduced_requirement_2 = _UnreducedRequirement()
        assert _RequirementCollection(
            unreduced_requirement_1, unreduced_requirement_2
        ).reduce() == _RequirementCollection(
            unreduced_requirement_1, unreduced_requirement_2
        )

    async def test_reduce__with_one_reduced_requirement(self) -> None:
        unreduced_requirement = _UnreducedRequirement()
        assert (
            _RequirementCollection(
                _ReducedToNoneRequirement(), unreduced_requirement
            ).reduce()
            == unreduced_requirement
        )

    async def test_reduce__with_all_reduced_requirements(self) -> None:
        assert (
            _RequirementCollection(
                _ReducedToNoneRequirement(), _ReducedToNoneRequirement()
            ).reduce()
            is None
        )

    async def test_reduce__with_reduced_similar_requirement_collection(self) -> None:
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
        return Plain(self.__class__.__name__)


class _ReduceToRequirementCollectionRequirementCollection(_RequirementCollection):
    @override
    def reduce(self) -> Requirement | None:
        return _RequirementCollection(*self._requirements)

    @override
    def summary(self) -> Localizable:
        return Plain(self.__class__.__name__)


class _MetRequirement(Requirement):
    @override
    def is_met(self) -> bool:
        return True

    @override
    def summary(self) -> Localizable:
        return Plain(self.__class__.__name__)


class _UnmetRequirement(Requirement):
    @override
    def is_met(self) -> bool:
        return False

    @override
    def summary(self) -> Localizable:
        return Plain(self.__class__.__name__)


class _ReducedToNoneRequirement(_MetRequirement):
    @override
    def reduce(self) -> Requirement | None:
        return None


class _UnreducedRequirement(_MetRequirement):
    pass


class TestAnyRequirement:
    async def test_is_met__with_one_met(self) -> None:
        assert AnyRequirement(
            _UnmetRequirement(), _UnmetRequirement(), _MetRequirement()
        ).is_met()

    async def test_is_met__without_any_met(self) -> None:
        assert not AnyRequirement(
            _UnmetRequirement(), _UnmetRequirement(), _UnmetRequirement()
        ).is_met()

    async def test_summary(self) -> None:
        assert (AnyRequirement().summary()).localize(DEFAULT_LOCALIZER)


class TestAllRequirements:
    async def test_is_met__with_all_but_one_met(self) -> None:
        assert not AllRequirements(
            _MetRequirement(), _MetRequirement(), _UnmetRequirement()
        ).is_met()

    async def test_is_met__with_all_met(self) -> None:
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


class TestStaticRequirement:
    def test_is_met(self) -> None:
        assert StaticRequirement(True, Plain("")).is_met()
        assert not StaticRequirement(False, Plain("")).is_met()

    def test_summary(self) -> None:
        summary = Plain("Hello, world!")
        assert StaticRequirement(True, summary).summary() is summary

    def test_details(self) -> None:
        details = Plain("Hello, world!")
        assert StaticRequirement(True, Plain(""), details).details() is details
