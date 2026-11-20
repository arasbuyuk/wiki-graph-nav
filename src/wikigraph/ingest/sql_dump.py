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
