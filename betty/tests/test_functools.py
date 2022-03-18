from typing import Any, List

from parameterized import parameterized

from betty.functools import walk, slice_to_range
from betty.tests import TestCase


class WalkTest(TestCase):
    class _Item:
        def __init__(self, child):
            self.child = child

    @parameterized.expand([
        (None,),
        (True,),
        (object(),),
        ([],),
    ])
    def test_with_invalid_attribute(self, item: Any) -> None:
        with self.assertRaises(AttributeError):
            list(walk(item, 'invalid_attribute_name'))

    def test_one_to_one_without_descendants(self) -> None:
        item = self._Item(None)
        actual = walk(item, 'child')
        expected = []
        self.assertEqual(expected, list(actual))

    def test_one_to_one_with_descendants(self) -> None:
        grandchild = self._Item(None)
        child = self._Item(grandchild)
        item = self._Item(child)
        actual = walk(item, 'child')
        expected = [child, grandchild]
        self.assertEqual(expected, list(actual))

    def test_one_to_many_without_descendants(self) -> None:
        item = self._Item([])
        actual = walk(item, 'child')
        expected = []
        self.assertEqual(expected, list(actual))

    def test_with_one_to_many_descendants(self) -> None:
        grandchild = self._Item([])
        child = self._Item([grandchild])
        item = self._Item([child])
        actual = walk(item, 'child')
        expected = [child, grandchild]
        self.assertEqual(expected, list(actual))

    def test_with_mixed_descendants(self) -> None:
        grandchild = self._Item([])
        child = self._Item(grandchild)
        item = self._Item([child])
        actual = walk(item, 'child')
        expected = [child, grandchild]
        self.assertEqual(expected, list(actual))


class SliceToRangeTest(TestCase):
    @parameterized.expand([
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, 16, 1)),
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, None, 1)),
        ([0], slice(None, 1, 1)),
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(None, None, 1)),
        ([9, 10, 11, 12, 13, 14, 15], slice(9, None, 1)),
        ([0, 3, 6, 9, 12, 15], slice(None, None, 3)),
        # Test a slice that is longer than the iterable.
        ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], slice(0, 99)),
    ])
    def test(self, expected_range_items: List[int], ranged_slice: slice) -> None:
        iterable = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        self.assertEqual(expected_range_items, list(slice_to_range(ranged_slice, iterable)))
