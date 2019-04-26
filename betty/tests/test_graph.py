from unittest import TestCase

from betty.graph import tsort, CyclicGraphError


class TSortTest(TestCase):
    def test_with_empty_graph(self):
        graph = {}
        self.assertCountEqual([], tsort(graph))

    def test_with_independent_vertices(self):
        graph = {
            1: set(),
            2: set(),
        }
        # Without edges we cannot assert the order.
        self.assertCountEqual([1, 2], tsort(graph))

    def test_with_dependent_vertices(self):
        graph = {
            1: {2},
        }
        self.assertEquals([1, 2], tsort(graph))

    def test_with_interdependent_vertices(self):
        graph = {
            1: {2},
            2: {1},
        }
        with self.assertRaises(CyclicGraphError):
            tsort(graph)
