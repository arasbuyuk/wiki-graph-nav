"""Stage 3: path search between two articles.

Done:
  - BFS baseline (shortest path in clicks, ground truth for evaluation)

TODO:
  - A* with pluggable heuristics
  - heuristic candidates: landmarks (ALT), embeddings / text similarity, category overlap
"""

from wikigraph.search.bfs import bfs
from wikigraph.search.result import SearchResult

__all__ = ["SearchResult", "bfs"]
