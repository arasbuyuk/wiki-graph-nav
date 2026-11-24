"""The Wikipedia link graph stored as CSR (Compressed Sparse Row) arrays."""

from pathlib import Path

import numpy as np
import pyarrow.parquet as pq


class Graph:
    """Directed graph of Wikipedia articles.

    Articles are numbered 0 ... n-1. We call that number the "index" of an article,
    to keep it apart from the Wikipedia page_id.

    The neighbours of index i are targets[offsets[i] : offsets[i + 1]].
    """

    def __init__(
        self, page_ids: np.ndarray, titles: list[str], offsets: np.ndarray, targets: np.ndarray
    ):
        self.page_ids = page_ids  # index -> page_id
        self.titles = titles  # index -> title
        self.offsets = offsets  # where the neighbours of each index start in targets
        self.targets = targets  # all neighbours, grouped by source
        self._title_to_index = {title: i for i, title in enumerate(titles)}

    @classmethod
    def from_edges(cls, page_ids, titles, sources, targets) -> "Graph":
        """Build the graph from page IDs, titles and an edge list of page IDs.

        page_ids must be sorted and unique, and titles[k] is the title of page_ids[k].
        Every edge endpoint must be one of the page_ids.
        """
        page_ids = np.asarray(page_ids, dtype=np.int64)
        sources = np.asarray(sources, dtype=np.int64)
        targets = np.asarray(targets, dtype=np.int64)
        titles = list(titles)
        n = len(page_ids)

        if n == 0:
            raise ValueError("graph needs at least one article")
        if len(titles) != n:
            raise ValueError("page_ids and titles must have the same length")
        if not np.all(np.diff(page_ids) > 0):
            raise ValueError("page_ids must be sorted and unique")

        # 1. Renumber: lookup array page_id -> index, -1 = not an article
        id_to_index = np.full(page_ids.max() + 1, -1, dtype=np.int32)
        id_to_index[page_ids] = np.arange(n, dtype=np.int32)
        src_idx = _to_index(sources, id_to_index)
        tgt_idx = _to_index(targets, id_to_index)

        # 2. CSR needs the edges grouped by source. Sort only if they aren't already.
        if not np.all(src_idx[:-1] <= src_idx[1:]):
            order = np.argsort(src_idx, kind="stable")
            src_idx = src_idx[order]
            tgt_idx = tgt_idx[order]

        # 3. offsets = 0 followed by the running sum of the out-degrees
        out_degree = np.bincount(src_idx, minlength=n)
        offsets = np.zeros(n + 1, dtype=np.int64)
        np.cumsum(out_degree, out=offsets[1:])

        return cls(page_ids, titles, offsets, tgt_idx)

    @classmethod
    def from_parquet(cls, folder: str | Path) -> "Graph":
        """Load pages.parquet and edges.parquet from the ingest stage."""
        folder = Path(folder)
        pages = pq.read_table(folder / "pages.parquet")
        edges = pq.read_table(folder / "edges.parquet")
        return cls.from_edges(
            pages["page_id"].to_numpy(),
            pages["title"].to_numpy(),
            edges["source"].to_numpy(),
            edges["target"].to_numpy(),
        )

    @property
    def num_nodes(self) -> int:
        return len(self.page_ids)

    @property
    def num_edges(self) -> int:
        return len(self.targets)

    def neighbours(self, i: int) -> np.ndarray:
        """Indices of the articles that article i links to (a view, no copy)."""
        return self.targets[self.offsets[i] : self.offsets[i + 1]]

    def out_degree(self, i: int) -> int:
        return int(self.offsets[i + 1] - self.offsets[i])

    def index_of(self, title: str) -> int:
        """Index of an article by title. Spaces are allowed: "United States" works."""
        key = title.replace(" ", "_")
        try:
            return self._title_to_index[key]
        except KeyError:
            raise KeyError(f"no article with title {title!r}") from None

    def title(self, i: int) -> str:
        return self.titles[i]

    def __repr__(self) -> str:
        return f"Graph({self.num_nodes:,} articles, {self.num_edges:,} edges)"


def _to_index(ids: np.ndarray, id_to_index: np.ndarray) -> np.ndarray:
    """Translate page_ids to indices. Fails if an id is not an article."""
    if len(ids) == 0:
        return np.zeros(0, dtype=np.int32)
    if ids.min() < 0 or ids.max() >= len(id_to_index):
        raise ValueError("edge endpoint is not an article")
    idx = id_to_index[ids]
    if (idx < 0).any():
        raise ValueError("edge endpoint is not an article")
    return idx
