"""Turn the parsed dump tables into the graph files pages.parquet and edges.parquet"""

from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from wikigraph.ingest.sql_dump import iter_linktargets, iter_pages, iter_redirects


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


def load_redirects(
    redirect_path: str | Path, title_to_id: dict[str, int], redirect_ids: set[int]
) -> tuple[dict[int, int], Counter]:
    """Map every usable namespace-0 redirect page to the page_id of its target article."""
    redirect_to_article: dict[int, int] = {}
    stats: Counter = Counter()

    for rd_from, ns, title, interwiki in iter_redirects(redirect_path):
        stats["rows"] += 1
        if rd_from not in redirect_ids:
            stats["not a ns-0 redirect page"] += 1
            continue
        if interwiki != "":
            stats["point to another wiki"] += 1
            continue
        if ns != 0:
            stats["target not in namespace 0"] += 1
            continue
        target = title_to_id[title]
        if target is None:
            stats["target page missing"] += 1
            continue
        if target in redirect_ids:
            stats["double redirect"] += 1
            continue
        redirect_to_article[rd_from] = target
        stats["usable"] += 1
    return redirect_to_article, stats


def resolve_linktargets(
    linktarget_path: str | Path,
    title_to_id: dict[str, int],
    redirect_ids: set[int],
    redirect_to_article: dict[int, int],
) -> tuple[dict[int, int], Counter]:
    """Map every link target that leads to an article to that article's page_id."""
    lt_to_article: dict[int, int] = {}
    stats: Counter = Counter()

    for lt_id, ns, title in iter_linktargets(linktarget_path):
        stats["rows"] += 1
        if ns != 0:
            stats["not namespace 0"] += 1
            continue
        page_id = title_to_id.get(title)
        if page_id is None:
            stats["red link"] += 1
            continue
        if page_id in redirect_ids:
            page_id = redirect_to_article.get(page_id)
            if page_id is None:
                stats["unusable redirect"] += 1
                continue
            stats["via redirect"] += 1
        else:
            stats["direct"] += 1
        lt_to_article[lt_id] = page_id
    return lt_to_article, stats
