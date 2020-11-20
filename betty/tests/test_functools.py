from typing import List, Any, Optional

from parameterized import parameterized

from betty.functools import walk_to_many
from betty.tests import TestCase


class WalkToManyTest(TestCase):
    class _ItemWithOneToMany:
        def __init__(self, children: List['Item']):
            self.children = children

    class _ItemWithOneToOne:
        def __init__(self, child: Optional['Item']):
            self.child = child

    @parameterized.expand([
        (None,),
        (True,),
        (object(),),
        ([],),
    ])
    def test_with_invalid_attribute(self, item: Any) -> None:
        with self.assertRaises(AttributeError):
            list(walk_to_many(item, 'invalid_attribute_name'))

    def test_without_descendants(self) -> None:
        item = self._ItemWithOneToMany([])
        actual = walk_to_many(item, 'children')
        expected = []
        self.assertEquals(expected, list(actual))

    def test_with_descendants(self) -> None:
        grandchild = self._ItemWithOneToMany([])
        child = self._ItemWithOneToMany([grandchild])
        item = self._ItemWithOneToMany([child])
        actual = walk_to_many(item, 'children')
        expected = [child, grandchild]
        self.assertEquals(expected, list(actual))
