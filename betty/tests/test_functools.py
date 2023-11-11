from typing import Any, Iterable

import pytest

from betty.functools import walk, slice_to_range


class TestWalk:
    class _Item:
        def __init__(self, child: 'TestWalk._Item | Iterable[TestWalk._Item] | None'):
            self.child = child

    @pytest.mark.parametrize('item', [
        None,
        True,
        object(),
        [],
    ])
    async def test_with_invalid_attribute(self, item: Any) -> None:
        with pytest.raises(AttributeError):
            list(walk(item, 'invalid_attribute_name'))

    async def test_one_to_one_without_descendants(self) -> None:
        item = self._Item(None)
        actual = walk(item, 'child')
        expected: list[None] = []
        assert expected == list(actual)

    async def test_one_to_one_with_descendants(self) -> None:
        grandchild = self._Item(None)
        child = self._Item(grandchild)
        item = self._Item(child)
        actual = walk(item, 'child')
        expected = [child, grandchild]
        assert expected == list(actual)

    async def test_one_to_many_without_descendants(self) -> None:
        item = self._Item([])
        actual = walk(item, 'child')
        expected: list[None] = []
        assert expected == list(actual)

    async def test_with_one_to_many_descendants(self) -> None:
        grandchild = self._Item([])
        child = self._Item([grandchild])
        item = self._Item([child])
        actual = walk(item, 'child')
        expected = [child, grandchild]
        assert expected == list(actual)

    async def test_with_mixed_descendants(self) -> None:
        grandchild = self._Item([])
        child = self._Item(grandchild)
        item = self._Item([child])
        actual = walk(item, 'child')
        expected = [child, grandchild]
        assert expected == list(actual)


class TestSliceToRange:
    @pytest.mark.parametrize('expected_range_items, ranged_slice', [
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, 16, 1)),
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, None, 1)),
        ([0], slice(None, 1, 1)),
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(None, None, 1)),
        ([9, 10, 11, 12, 13, 14, 15], slice(9, None, 1)),
        ([0, 3, 6, 9, 12, 15], slice(None, None, 3)),
        # Test a slice that is longer than the iterable.
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, 99)),
    ])
    async def test(self, expected_range_items: list[int], ranged_slice: slice) -> None:
        iterable = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        assert expected_range_items == list(slice_to_range(ranged_slice, iterable))
