"""Breadth-first search: shortest path in clicks. The ground truth for A*."""

from collections import deque

import numpy as np

from wikigraph.graph import Graph
from wikigraph.search.result import SearchResult


def bfs(graph: Graph, start: int, goal: int) -> SearchResult:
    """Find a shortest path (fewest clicks) from start to goal. Both are article indices."""
    n = graph.num_nodes
    for name, i in (("start", start), ("goal", goal)):
        if not 0 <= i < n:
            raise IndexError(f"{name} index {i} is outside the graph (0 ... {n - 1})")

    if start == goal:
        return SearchResult(path=[start], expanded=0)

    # parent[j] = the article we reached j from; -1 = not reached yet.
    # The start is its own parent, which also marks it as reached.
    parent = np.full(n, -1, dtype=np.int32)
    parent[start] = start
    queue = deque([start])
    expanded = 0

    while queue:
        u = queue.popleft()
        expanded += 1

        nbrs = graph.neighbours(u)
        new = np.unique(nbrs[parent[nbrs] == -1])
        if len(new) == 0:
            continue
        parent[new] = u

        # Goal check when the goal is first reached, not when it's taken out of the
        # queue. In BFS the first time is already on a shortest path, so we can stop
        # one layer earlier.
        if parent[goal] != -1:
            return SearchResult(path=_walk_back(parent, start, goal), expanded=expanded)

        queue.extend(new.tolist())

    return SearchResult(path=None, expanded=expanded)


def _walk_back(parent: np.ndarray, start: int, goal: int) -> list[int]:
    """Follow the parent links from goal back to start, then reverse."""
    path = [goal]
    while path[-1] != start:
        path.append(int(parent[path[-1]]))
    path.reverse()
    return path
