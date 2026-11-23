"""Read rows from Wikipedia SQL dump files"""

import csv
import gzip
from _collections_abc import Iterator
from pathlib import Path


def split_row(line: str) -> list[str]:
    """Split one row line into its values, as strings. Commas inside quotes are kept."""
    body = line.rstrip("\n")[1:-2]
    return next(csv.reader([body], quotechar="'", escapechar="\\"))


def iter_rows(path: str | Path) -> Iterator[list[str]]:
    """Yield every row of a dump file, one at a time."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("("):
                yield split_row(line)


def iter_pages(path: str | Path) -> Iterator[tuple[int, int, str, bool]]:
    """Yield (page_id, namespace, title, is_redirect) for every row of the page table."""
    for values in iter_rows(path):
        yield int(values[0]), int(values[1]), values[2], int(values[3]) == 1


def iter_linktargets(path: str | Path) -> Iterator[tuple[int, int, str]]:
    """Yield (lt_id, namespace, title) for every row of the linktarget table."""
    for values in iter_rows(path):
        yield int(values[0]), int(values[1]), values[2]


def iter_redirects(path: str | Path) -> Iterator[tuple[int, int, str, str]]:
    """Yield (rd_from, namespace, title, interwiki) for every row of the redirect table.
    interwiki is "" for redirects within this wiki. The fragment column is not returned.
    """
    for values in iter_rows(path):
        yield int(values[0]), int(values[1]), values[2], values[3]


def iter_pagelinks(path: str | Path) -> Iterator[tuple[int, int, int]]:
    """Yield (pl_from, from_namespace, target_id) for every row of the pagelinks table."""
    for values in iter_rows(path):
        yield int(values[0]), int(values[1]), int(values[2])
