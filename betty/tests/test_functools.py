from typing import Any

from parameterized import parameterized

from betty.functools import walk
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
        self.assertEquals(expected, list(actual))

    def test_one_to_one_with_descendants(self) -> None:
        grandchild = self._Item(None)
        child = self._Item(grandchild)
        item = self._Item(child)
        actual = walk(item, 'child')
        expected = [child, grandchild]
        self.assertEquals(expected, list(actual))

    def test_one_to_many_without_descendants(self) -> None:
        item = self._Item([])
        actual = walk(item, 'child')
        expected = []
        self.assertEquals(expected, list(actual))

    def test_with_one_to_many_descendants(self) -> None:
        grandchild = self._Item([])
        child = self._Item([grandchild])
        item = self._Item([child])
        actual = walk(item, 'child')
        expected = [child, grandchild]
        self.assertEquals(expected, list(actual))

    def test_with_mixed_descendants(self) -> None:
        grandchild = self._Item([])
        child = self._Item(grandchild)
        item = self._Item([child])
        actual = walk(item, 'child')
        expected = [child, grandchild]
        self.assertEquals(expected, list(actual))
