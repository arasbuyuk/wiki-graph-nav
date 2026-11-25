"""Tests for BFS: small hand-made graphs, plus random graphs checked against Floyd-Warshall."""

from itertools import pairwise

import numpy as np
import pytest

from wikigraph.graph import Graph
from wikigraph.search import bfs

# A -> B, A -> C, B -> C, C -> A (the example from the CSR tests), plus D with no
# incoming links, so nothing can reach it.
PAGE_IDS = [2, 5, 9, 12]
TITLES = ["A", "B", "C", "D"]
SOURCES = [2, 2, 5, 9, 12]
TARGETS = [5, 9, 9, 2, 2]


@pytest.fixture
def g() -> Graph:
    return Graph.from_edges(PAGE_IDS, TITLES, SOURCES, TARGETS)


def path_titles(g, result):
    return [g.title(i) for i in result.path]


def test_direct_link(g):
    r = bfs(g, g.index_of("A"), g.index_of("B"))
    assert path_titles(g, r) == ["A", "B"]
    assert r.hops == 1
    assert r.expanded == 1  # found while looking at A's links, so it stopped right away


def test_two_clicks(g):
    r = bfs(g, g.index_of("B"), g.index_of("A"))
    assert path_titles(g, r) == ["B", "C", "A"]
    assert r.hops == 2


def test_start_is_goal(g):
    a = g.index_of("A")
    r = bfs(g, a, a)
    assert r.path == [a]
    assert r.hops == 0
    assert r.expanded == 0


def test_unreachable(g):
    r = bfs(g, g.index_of("A"), g.index_of("D"))
    assert not r.found
    assert r.path is None
    assert r.hops is None
    assert r.expanded == 3  # A, B and C were all looked at before giving up


def test_takes_the_shortcut():
    # Long way 0 -> 1 -> 2 -> 3 -> 4, shortcut 0 -> 5 -> 4
    g = Graph.from_edges(range(6), list("abcdef"), [0, 1, 2, 3, 0, 5], [1, 2, 3, 4, 5, 4])
    assert bfs(g, 0, 4).path == [0, 5, 4]


def test_self_loops_and_duplicate_edges():
    # The ingest removes these, but BFS shouldn't depend on that
    g = Graph.from_edges([0, 1, 2], list("abc"), [0, 0, 0, 1], [0, 1, 1, 2])
    r = bfs(g, 0, 2)
    assert r.path == [0, 1, 2]
    assert r.expanded == 2


def test_invalid_index(g):
    with pytest.raises(IndexError):
        bfs(g, 0, 4)
    with pytest.raises(IndexError):
        bfs(g, -1, 0)


def floyd_warshall(n, sources, targets):
    """All-pairs shortest distances, computed in a completely different way than BFS."""
    dist = np.full((n, n), np.inf)
    np.fill_diagonal(dist, 0)
    dist[sources, targets] = np.minimum(dist[sources, targets], 1)
    for k in range(n):
        dist = np.minimum(dist, dist[:, [k]] + dist[[k], :])
    return dist


@pytest.mark.parametrize("seed", range(5))
def test_random_graphs_match_floyd_warshall(seed):
    rng = np.random.default_rng(seed)
    n, m = 25, 50
    sources = rng.integers(0, n, m)
    targets = rng.integers(0, n, m)
    g = Graph.from_edges(range(n), [str(i) for i in range(n)], sources, targets)
    dist = floyd_warshall(n, sources, targets)
    edges = set(zip(sources.tolist(), targets.tolist(), strict=True))

    for s in range(n):
        for t in range(n):
            r = bfs(g, s, t)
            if np.isinf(dist[s, t]):
                assert not r.found
            else:
                assert r.hops == dist[s, t]
                assert r.path[0] == s and r.path[-1] == t
                # every step of the path must be a real link
                assert all((a, b) in edges for a, b in pairwise(r.path))
