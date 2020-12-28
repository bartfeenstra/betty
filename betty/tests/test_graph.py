from betty.graph import CyclicGraphError, tsort_grouped
from betty.tests import TestCase


class TsortGroupedTest(TestCase):
    def test_with_empty_graph(self):
        graph = {}
        self.assertCountEqual([], tsort_grouped(graph))

    def test_with_isolated_vertices(self):
        graph = {
            1: set(),
            2: set(),
        }
        # Without edges we cannot assert the order.
        self.assertEquals([{1, 2}], tsort_grouped(graph))

    def test_with_edges(self):
        graph = {
            1: {2},
        }
        self.assertEquals([{1}, {2}], tsort_grouped(graph))

    def test_with_isolated_vertices_and_edges(self):
        graph = {
            1: {2, 3, 4},
            5: {4, 6, 7},
            8: set(),
            9: set(),
        }
        vertex_groups = tsort_grouped(graph)
        self.assertEquals([
            {8, 9},
            {1, 5},
            {2, 3, 4, 6, 7},
        ], vertex_groups)

    def test_with_multiple_chained_edges(self):
        graph = {
            2: {3},
            1: {2},
        }
        self.assertEquals([{1}, {2}, {3}], tsort_grouped(graph))

    def test_with_multiple_indegrees(self):
        graph = {
            1: {3},
            2: {3},
        }
        vertex_groups = tsort_grouped(graph)
        self.assertEquals([
            {1, 2},
            {3},
        ], vertex_groups)

    def test_with_multiple_outdegrees(self):
        graph = {
            1: {2, 3},
        }
        vertex_groups = tsort_grouped(graph)
        self.assertEquals([
            {1},
            {2, 3},
        ], vertex_groups)

    def test_with_cyclic_edges(self):
        graph = {
            1: {2},
            2: {1},
        }
        with self.assertRaises(CyclicGraphError):
            tsort_grouped(graph)
