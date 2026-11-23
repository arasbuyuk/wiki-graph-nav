"""Turn the parsed dump tables into the graph files pages.parquet and edges.parquet"""

from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from wikigraph.ingest.sql_dump import iter_pages


def load_page_index(page_path: str | Path) -> tuple[dict[str, int], set[int], Counter]:
    """Read the page table once.

    Returns:
        title_to_id: every namespace-0 title (articles AND redirects) -> page_id
        redirect_ids: page_ids of the namespace-0 redirect pages
        stats: counts of what we saw, so we can check the numbers
    """

    title_to_id: dict[str, int] = {}
    redirect_ids: set[int] = set()
    stats: Counter = Counter()

    for page_id, ns, title, is_redirect in iter_pages(page_path):
        stats["rows"] += 1
        if ns != 0:
            stats["not namespace 0"] += 1
            continue
        if title in title_to_id:
            stats["duplicate title"] += 1
            continue
        title_to_id[title] = page_id
        if is_redirect:
            redirect_ids.add(page_id)
            stats["redirects"] += 1
        else:
            stats["articles"] += 1
    return title_to_id, redirect_ids, stats


def write_pages(title_to_id: dict[str, int], redirect_ids: set[int], out_path: str | Path) -> int:
    """Write all articles (namespace 0, not redirects) to a parquet file, sorted by page_id.

    Returns the number of rows written.
    """
    rows = sorted(
        (page_id, title) for title, page_id in title_to_id.items() if page_id not in redirect_ids
    )
    table = pa.table(
        {
            "page_id": pa.array([page_id for page_id, _ in rows], type=pa.int64()),
            "title": pa.array([title for _, title in rows], type=pa.string()),
        }
    )
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
    return table.num_rows
