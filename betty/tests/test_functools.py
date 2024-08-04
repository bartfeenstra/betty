from collections.abc import Awaitable, Callable, Iterable, Sequence
from typing import Any, TypeVar

import pytest

from betty.functools import slice_to_range, Do, Uniquifier

_T = TypeVar("_T")


class TestSliceToRange:
    @pytest.mark.parametrize(
        ("expected_range_items", "ranged_slice"),
        [
            ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, 16, 1)),
            ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, None, 1)),
            ([0], slice(None, 1, 1)),
            (
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                slice(None, None, 1),
            ),
            ([9, 10, 11, 12, 13, 14, 15], slice(9, None, 1)),
            ([0, 3, 6, 9, 12, 15], slice(None, None, 3)),
            # Test a slice that is longer than the iterable.
            ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, 99)),
        ],
    )
    async def test(
        self, expected_range_items: Sequence[int], ranged_slice: slice
    ) -> None:
        iterable = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        assert expected_range_items == list(slice_to_range(ranged_slice, iterable))


class TestDo:
    _RESULT = 123456789

    class _DoException(RuntimeError):
        pass

    class _ConditionException(AssertionError):
        pass

    async def _do_success(self, result: int) -> int:
        return result

    def _build_do_success_after_tries(
        self, tries: int
    ) -> Callable[[int], Awaitable[int]]:
        async def __build_do_success_after_retries(result: int) -> int:
            nonlocal tries

            while True:
                tries -= 1
                if tries == 0:
                    return await self._do_success(result)
                else:
                    await self._do_raise_exception()

        return __build_do_success_after_retries

    async def _do_raise_exception(self) -> int:
        raise self._DoException

    def _condition_success(self, result: int) -> None:
        return None

    def _condition_raise_exception(self, result: int) -> None:
        raise self._ConditionException

    def _condition_return_false(self, result: int) -> False:
        return False

    async def test_until_should_return(self) -> None:
        assert (
            await Do[Any, int](self._do_success, self._RESULT).until() == self._RESULT
        )

    async def test_until_should_return_after_retries(self) -> None:
        assert (
            await Do[Any, int](
                self._build_do_success_after_tries(2), self._RESULT
            ).until()
            == self._RESULT
        )

    async def test_until_raises_exception(self) -> None:
        with pytest.raises(self._DoException):
            await Do[Any, int](self._do_raise_exception).until()

    async def test_until_condition_raises_exception(self) -> None:
        with pytest.raises(self._ConditionException):
            await Do[Any, int](self._do_success, self._RESULT).until(
                self._condition_raise_exception
            )

    async def test_until_condition_returns_false(self) -> None:
        with pytest.raises(RuntimeError):
            await Do[Any, int](self._do_success, self._RESULT).until(
                self._condition_return_false
            )

    async def test_until_retries_exceeded_raises_exception(self) -> None:
        with pytest.raises(self._DoException):
            await Do[Any, int](self._do_raise_exception).until(
                retries=1, timeout=999999999
            )

    async def test_until_timeout_exceeded_raises_exception(self) -> None:
        with pytest.raises(self._DoException):
            await Do[Any, int](self._do_raise_exception).until(
                timeout=0, retries=999999999
            )


class TestUniquifier:
    @pytest.mark.parametrize(
        ("expected", "values", "key"),
        [
            ([], [], None),
            ([], [[]], None),
            (["one"], [["one"]], None),
            (["one"], [["one", "one"]], None),
            (["one", "two"], [["one", "two"]], None),
            (["one", "two"], [["one", "two", "one"]], None),
            (["one"], [["one"], ["one"]], None),
            (["one", "two"], [["one"], ["one", "two"]], None),
            (["one", "two"], [["one"], ["one", "two", "one"]], None),
            (
                ["aaa", "bbb", "ccc"],
                [["aaa", "abc", "bbb", "bob", "ccc", "coo"]],
                lambda value: value[0],
            ),
        ],
    )
    async def test(
        self,
        expected: Sequence[_T],
        values: Iterable[Iterable[_T]],
        key: Callable[[_T], Any] | None,
    ) -> None:
        sut = Uniquifier(*values, key=key)
        assert list(sut) == expected
