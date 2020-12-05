from typing import Iterable, Tuple, Set, Dict, List, Hashable

Vertex = Hashable
Edge = Tuple[Vertex, Vertex]
Graph = Dict[Vertex, Set[Vertex]]


class GraphError(BaseException):
    pass  # pragma: no cover


class CyclicGraphError(GraphError):
    pass  # pragma: no cover


def tsort_grouped(graph: Graph) -> List[Set[Vertex]]:
    """
    Sorts a graph topologically.

    This function uses the algorithm described by Kahn (1962), with the following additional properties:

    * Stable for stable graphs (sorted dictionaries).
    * Optimized for concurrent processing: each item of the returned first-level list is a second-level list of vertices
      that can be processed concurrently. Second-level lists are sorted to optimize (reduce) total processing time.
    """
    edges = list(_graph_to_edges(graph))
    sorted_vertices = set()
    sorted_vertex_groups = []
    upcoming_outdegree_vertices = []
    while True:
        outdegree_vertices = upcoming_outdegree_vertices + [edge[0] for edge in edges if not _is_target(edge[0], edges)]
        upcoming_outdegree_vertices = []
        if not outdegree_vertices:
            break
        sorted_vertex_group = set()
        for outdegree_vertex in outdegree_vertices:
            if outdegree_vertex not in sorted_vertices:
                sorted_vertices.add(outdegree_vertex)
                sorted_vertex_group.add(outdegree_vertex)
            outdegree_vertex_edges = list([edge for edge in edges if edge[0] == outdegree_vertex])
            for edge in outdegree_vertex_edges:
                edges.remove(edge)
                if not _is_target(edge[1], edges):
                    upcoming_outdegree_vertices.append(edge[1])
        sorted_vertex_groups.append(sorted_vertex_group)

    if edges:
        raise CyclicGraphError

    isolated_vertices = {vertex for vertex in graph.keys() if vertex not in sorted_vertices}
    if isolated_vertices:
        return [isolated_vertices] + sorted_vertex_groups
    return sorted_vertex_groups


def _graph_to_edges(graph: Graph) -> Iterable[Edge]:
    for from_vertex, to_vertices in graph.items():
        for to_vertex in to_vertices:
            yield from_vertex, to_vertex


def _is_target(vertex: Vertex, edges: Iterable[Edge]) -> bool:
    for edge in edges:
        if vertex == edge[1]:
            return True
    return False
