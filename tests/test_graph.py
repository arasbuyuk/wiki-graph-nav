"""Tests for the CSR graph, on tiny graphs where we know every answer."""

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from wikigraph.graph import Graph

# The example from the notebook: A -> B, A -> C, B -> C, C -> A.
# The page_ids have gaps on purpose, like the real ones.
PAGE_IDS = [2, 5, 9]
TITLES = ["A", "B", "C"]
SOURCES = [2, 2, 5, 9]
TARGETS = [5, 9, 9, 2]


@pytest.fixture
def abc() -> Graph:
    return Graph.from_edges(PAGE_IDS, TITLES, SOURCES, TARGETS)


def test_csr_arrays(abc):
    assert abc.offsets.tolist() == [0, 2, 3, 4]
    assert abc.targets.tolist() == [1, 2, 2, 0]


def test_sizes(abc):
    assert abc.num_nodes == 3
    assert abc.num_edges == 4


def test_neighbours(abc):
    a, b, c = abc.index_of("A"), abc.index_of("B"), abc.index_of("C")
    assert abc.neighbours(a).tolist() == [b, c]
    assert abc.neighbours(b).tolist() == [c]
    assert abc.neighbours(c).tolist() == [a]
    assert abc.out_degree(a) == 2


def test_unsorted_edges_give_the_same_graph(abc):
    shuffled = Graph.from_edges(PAGE_IDS, TITLES, SOURCES[::-1], TARGETS[::-1])
    assert shuffled.offsets.tolist() == abc.offsets.tolist()
    for i in range(abc.num_nodes):
        assert sorted(shuffled.neighbours(i).tolist()) == sorted(abc.neighbours(i).tolist())


def test_article_without_links():
    # D (page_id 12) has no outgoing links: its block in targets is empty
    g = Graph.from_edges([2, 5, 12], ["A", "B", "D"], [2], [5])
    d = g.index_of("D")
    assert g.out_degree(d) == 0
    assert g.neighbours(d).tolist() == []
    assert g.offsets.tolist() == [0, 1, 1, 1]


def test_titles_with_spaces():
    g = Graph.from_edges([1, 2], ["United_States", "Munich"], [1], [2])
    assert g.index_of("United States") == g.index_of("United_States") == 0
    assert g.title(1) == "Munich"


def test_unknown_title(abc):
    with pytest.raises(KeyError, match="no article"):
        abc.index_of("Atlantis")


@pytest.mark.parametrize("bad_target", [7, 100, -1])
def test_edge_to_non_article_is_rejected(bad_target):
    # 7 is inside the id range but not an article, 100 and -1 are outside of it
    with pytest.raises(ValueError, match="not an article"):
        Graph.from_edges(PAGE_IDS, TITLES, [2], [bad_target])


def test_unsorted_page_ids_are_rejected():
    with pytest.raises(ValueError, match="sorted"):
        Graph.from_edges([5, 2, 9], TITLES, SOURCES, TARGETS)


def test_from_parquet(tmp_path, abc):
    pq.write_table(
        pa.table({"page_id": pa.array(PAGE_IDS, pa.int64()), "title": TITLES}),
        tmp_path / "pages.parquet",
    )
    pq.write_table(
        pa.table(
            {"source": pa.array(SOURCES, pa.int64()), "target": pa.array(TARGETS, pa.int64())}
        ),
        tmp_path / "edges.parquet",
    )
    g = Graph.from_parquet(tmp_path)
    assert np.array_equal(g.offsets, abc.offsets)
    assert np.array_equal(g.targets, abc.targets)
    assert g.titles == TITLES
