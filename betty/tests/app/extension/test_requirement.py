from typing import Optional

import pytest

from betty.app import App
from betty.app.extension import Requirement
from betty.app.extension.requirement import RequirementCollection, RequirementError, AllRequirements, AnyRequirement


class TestRequirement:
    def test_assert_met_should_raise_error_if_unmet(self) -> None:
        class _Requirement(Requirement):
            def summary(self) -> str:
                return 'Lorem ipsum'

            def is_met(self) -> bool:
                return False
        with pytest.raises(RequirementError):
            _Requirement().assert_met()

    def test_assert_met_should_do_nothing_if_met(self) -> None:
        class _Requirement(Requirement):
            def is_met(self) -> bool:
                return True
        _Requirement().assert_met()

    def test___str___with_details(self) -> None:
        class _Requirement(Requirement):
            def summary(self) -> str:
                return 'Lorem ipsum'

            def details(self) -> str:
                return 'Dolor sit amet'
        assert 'Lorem ipsum\n-----------\nDolor sit amet' == str(_Requirement())

    def test___str___without_details(self) -> None:
        class _Requirement(Requirement):
            def summary(self) -> str:
                return 'Lorem ipsum'
        assert 'Lorem ipsum' == str(_Requirement())


class TestRequirementCollection:
    def test___eq___with_incomparable_type(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass

        assert _RequirementCollection() != 123

    def test___eq___with_empty_collections(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass

        assert _RequirementCollection() == _RequirementCollection()

    def test___eq___with_non_empty_collections(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass

        class _Requirement(Requirement):
            pass

        requirement_1 = _Requirement()
        requirement_2 = _Requirement()
        assert _RequirementCollection(requirement_1, requirement_2) == _RequirementCollection(requirement_1, requirement_2)

    def test___add__(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass

        class _Requirement(Requirement):
            pass

        requirement_1 = _Requirement()
        requirement_2 = _Requirement()
        sut = _RequirementCollection(requirement_1)
        sut += requirement_2
        assert [requirement_1, requirement_2] == sut._requirements

    def test___str___without_requirements(self) -> None:
        class _RequirementCollection(RequirementCollection):
            def summary(self) -> str:
                return 'Lorem ipsum'
        assert 'Lorem ipsum' == str(_RequirementCollection())

    def test___str___with_requirements(self) -> None:
        class _RequirementCollection(RequirementCollection):
            def summary(self) -> str:
                return 'Lorem ipsum'

        class _Requirement(Requirement):
            def summary(self) -> str:
                return 'Lorem ipsum'
        assert 'Lorem ipsum\n- Lorem ipsum' == str(_RequirementCollection(_Requirement()))

    def test_reduce_without_requirements(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass
        assert _RequirementCollection().reduce() is None

    def test_reduce_without_reduced_requirements(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass

        class _UnreducedRequirement(Requirement):
            pass

        unreduced_requirement_1 = _UnreducedRequirement()
        unreduced_requirement_2 = _UnreducedRequirement()
        assert _RequirementCollection(unreduced_requirement_1, unreduced_requirement_2).reduce() == _RequirementCollection(unreduced_requirement_1, unreduced_requirement_2)

    def test_reduce_with_one_reduced_requirement(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass

        class _UnreducedRequirement(Requirement):
            pass

        class _ReducedToNoneRequirement(Requirement):
            def reduce(self) -> Optional[Requirement]:
                return None

        unreduced_requirement = _UnreducedRequirement()
        assert _RequirementCollection(_ReducedToNoneRequirement(), unreduced_requirement).reduce() == unreduced_requirement

    def test_reduce_with_all_reduced_requirements(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass

        class _ReducedToNoneRequirement(Requirement):
            def reduce(self) -> Optional[Requirement]:
                return None
        assert _RequirementCollection(_ReducedToNoneRequirement(), _ReducedToNoneRequirement()).reduce() is None

    def test_reduce_with_reduced_similar_requirement_collection(self) -> None:
        class _RequirementCollection(RequirementCollection):
            pass

        class _Requirement(Requirement):
            pass
        requirement_1 = _Requirement()
        requirement_2 = _Requirement()
        assert _RequirementCollection(_RequirementCollection(requirement_1), requirement_2).reduce() == _RequirementCollection(requirement_1, requirement_2)


class TestAnyRequirement:
    def test_is_met_with_one_met(self) -> None:
        class _MetRequirement(Requirement):
            def is_met(self) -> bool:
                return True

        class _UnmetRequirement(Requirement):
            def is_met(self) -> bool:
                return False

        with App():
            assert AnyRequirement(_UnmetRequirement(), _UnmetRequirement(), _MetRequirement()).is_met()

    def test_is_met_without_any_met(self) -> None:
        class _UnmetRequirement(Requirement):
            def is_met(self) -> bool:
                return False

        with App():
            assert not AnyRequirement(_UnmetRequirement(), _UnmetRequirement(), _UnmetRequirement()).is_met()

    def test_summary(self) -> None:
        with App():
            assert isinstance(AnyRequirement().summary(), str)


class TestAllRequirements:
    def test_is_met_with_all_but_one_met(self) -> None:
        class _MetRequirement(Requirement):
            def is_met(self) -> bool:
                return True

        class _UnmetRequirement(Requirement):
            def is_met(self) -> bool:
                return False

        with App():
            assert not AllRequirements(_MetRequirement(), _MetRequirement(), _UnmetRequirement()).is_met()

    def test_is_met_with_all_met(self) -> None:
        class _MetRequirement(Requirement):
            def is_met(self) -> bool:
                return True

        with App():
            assert AllRequirements(_MetRequirement(), _MetRequirement(), _MetRequirement()).is_met()

    def test_summary(self) -> None:
        with App():
            assert isinstance(AllRequirements().summary(), str)
