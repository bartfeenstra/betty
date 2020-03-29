from typing import Iterable, Any, Tuple, Set, Dict

Vertex = Any
Edge = Tuple[Vertex, Vertex]
Graph = Dict[Vertex, Set[Vertex]]


class GraphError(BaseException):
    pass  # pragma: no cover


class CyclicGraphError(GraphError):
    pass  # pragma: no cover


def tsort(graph: Graph) -> Iterable[Vertex]:
    edges = list(_graph_to_edges(graph))
    sorted_vertices = []
    outdegree_vertices = list(
        [edge[0] for edge in edges if not _is_target(edge[0], edges)])
    while outdegree_vertices:
        outdegree_vertex = outdegree_vertices.pop()
        if outdegree_vertex not in sorted_vertices:
            sorted_vertices.append(outdegree_vertex)
        outdegree_vertex_edges = list(
            [edge for edge in edges if edge[0] == outdegree_vertex])
        while outdegree_vertex_edges:
            edge = outdegree_vertex_edges.pop()
            edges.remove(edge)
            if not _is_target(edge[1], edges):
                outdegree_vertices.append(edge[1])
    if edges:
        raise CyclicGraphError
    isolated_vertices = list(graph.keys() - sorted_vertices)
    return sorted_vertices + isolated_vertices


def _graph_to_edges(graph: Graph) -> Iterable[Edge]:
    for from_vertex, to_vertices in graph.items():
        for to_vertex in to_vertices:
            yield from_vertex, to_vertex


def _is_target(vertex: Vertex, edges: Iterable[Edge]) -> bool:
    for edge in edges:
        if vertex == edge[1]:
            return True
    return False
