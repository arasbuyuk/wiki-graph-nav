"""What a path search returns. Shared by BFS and A*, so they can be compared."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    """Result of one search from a start article to a goal article.

    path:     article indices from start to goal (both included), or None if the goal
              can't be reached from the start.
    expanded: how many articles the search took out of its queue and looked at the
              links of. This is the main cost measure for comparing BFS with A*.
    """

    path: list[int] | None
    expanded: int

    @property
    def found(self) -> bool:
        return self.path is not None

    @property
    def hops(self) -> int:
        """Number of clicks on the path (one less than the number of articles)."""
        return None if self.path is None else len(self.path) - 1
