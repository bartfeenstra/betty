from betty.graph import tsort, CyclicGraphError
from betty.tests import TestCase


class TSortTest(TestCase):
    def test_with_empty_graph(self):
        graph = {}
        self.assertCountEqual([], tsort(graph))

    def test_with_isolated_vertices(self):
        graph = {
            1: set(),
            2: set(),
        }
        # Without edges we cannot assert the order.
        self.assertCountEqual([1, 2], tsort(graph))

    def test_with_edges(self):
        graph = {
            1: {2},
        }
        self.assertEquals([1, 2], tsort(graph))

    def test_with_multiple_chained_edges(self):
        graph = {
            2: {3},
            1: {2},
        }
        self.assertEquals([1, 2, 3], tsort(graph))

    def test_with_multiple_indegrees(self):
        graph = {
            1: {3},
            2: {3},
        }
        vertices = tsort(graph)
        self.assertEquals(3, len(vertices))
        self.assertIn(1, vertices)
        self.assertIn(2, vertices)
        self.assertEquals(3, vertices[2])

    def test_with_multiple_outdegrees(self):
        graph = {
            1: {2, 3},
        }
        vertices = tsort(graph)
        self.assertEquals(3, len(vertices))
        self.assertEquals(1, vertices[0])
        self.assertIn(2, vertices)
        self.assertIn(3, vertices)

    def test_with_cyclic_edges(self):
        graph = {
            1: {2},
            2: {1},
        }
        with self.assertRaises(CyclicGraphError):
            tsort(graph)
