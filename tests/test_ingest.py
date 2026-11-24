"""Tests for the ingest stage, on a tiny hand-made wiki where we know every answer."""

import gzip

import pyarrow.parquet as pq
import pytest

from wikigraph.ingest.build import (
    build_edges,
    load_page_index,
    load_redirects,
    resolve_linktargets,
    write_edges,
    write_pages,
)
from wikigraph.ingest.sql_dump import split_row

# Each table is written in the same format as the real dumps: one row per line,
# starting with "(" and ending with ")," (or ");" for the last row).
PAGE_ROWS = [
    "(1,0,'Munich',0,0)",
    "(2,0,'Bavaria',0,0)",
    "(3,0,'Germany',0,0)",
    "(4,0,'Isar',0,0)",  # article that nobody links to
    "(10,0,'Bayern',1,0)",  # redirect -> Bavaria
    "(11,0,'Muenchen',1,0)",  # redirect -> Munich
    "(12,0,'Old_Name',1,0)",  # broken redirect: its target page does not exist
    "(13,0,'Muenchen_(de)',1,0)",  # redirect into another wiki
    "(14,0,'BRD',1,0)",  # double redirect: BRD -> Deutschland -> Germany
    "(15,0,'Deutschland',1,0)",  # redirect -> Germany
    "(16,0,'Cities',1,0)",  # redirect into the Category namespace
    "(20,14,'Cities_in_Germany',0,0)",  # a category page, not an article
]

REDIRECT_ROWS = [
    "(10,0,'Bavaria','','')",
    "(11,0,'Munich','','')",
    "(12,0,'Deleted_Page','','')",
    "(13,0,'München','de','')",
    "(14,0,'Deutschland','','')",
    "(15,0,'Germany','','')",
    "(16,14,'Cities_in_Germany','','')",
    "(99,0,'Germany','','')",  # rd_from is not a namespace-0 redirect page
]

LINKTARGET_ROWS = [
    "(100,0,'Bavaria')",
    "(101,0,'Bayern')",
    "(102,0,'Munich')",
    "(103,0,'Muenchen')",
    "(104,0,'Nowhere')",
    "(105,0,'Old_Name')",
    "(106,14,'Cities_in_Germany')",
    "(107,0,'Germany')",
    "(108,0,'BRD')",
]

PAGELINKS_ROWS = [
    "(1,0,100)",  # Munich -> Bavaria
    "(1,0,101)",  # Munich -> Bayern -> Bavaria (duplicate of the row above)
    "(1,0,103)",  # Munich -> Muenchen -> Munich (self loop)
    "(1,0,104)",  # Munich -> red link
    "(1,0,107)",  # Munich -> Germany
    "(2,0,102)",  # Bavaria -> Munich
    "(2,0,107)",  # Bavaria -> Germany
    "(3,0,108)",  # Germany -> BRD (double redirect, dropped)
    "(3,0,106)",  # Germany -> a category
    "(10,0,107)",  # source is a redirect
    "(20,14,102)",  # source is a category page
    "(999,0,102)",  # source page does not exist
]


def write_dump(path, table, rows):
    """Write rows as a gzipped SQL dump, the way Wikimedia does."""
    lines = [f"INSERT INTO `{table}` VALUES"]
    lines += [row + "," for row in rows[:-1]]
    lines.append(rows[-1] + ";")
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


@pytest.fixture
def dumps(tmp_path):
    """Create the four fake dump files and return their paths."""
    return {
        "page": write_dump(tmp_path / "page.sql.gz", "page", PAGE_ROWS),
        "redirect": write_dump(tmp_path / "redirect.sql.gz", "redirect", REDIRECT_ROWS),
        "linktarget": write_dump(tmp_path / "linktarget.sql.gz", "linktarget", LINKTARGET_ROWS),
        "pagelinks": write_dump(tmp_path / "pagelinks.sql.gz", "pagelinks", PAGELINKS_ROWS),
    }


def test_split_row_handles_escaped_quotes_and_commas():
    line = "(7,0,'Rock_\\'n\\'_Roll,_Baby',0),\n"
    assert split_row(line) == ["7", "0", "Rock_'n'_Roll,_Baby", "0"]


def test_load_page_index(dumps):
    title_to_id, redirect_ids, stats = load_page_index(dumps["page"])

    assert title_to_id["Munich"] == 1
    assert "Cities_in_Germany" not in title_to_id
    assert redirect_ids == {10, 11, 12, 13, 14, 15, 16}
    assert stats["articles"] == 4
    assert stats["redirects"] == 7
    assert stats["not namespace 0"] == 1


def test_load_redirects(dumps):
    title_to_id, redirect_ids, _ = load_page_index(dumps["page"])
    redirect_to_article, stats = load_redirects(dumps["redirect"], title_to_id, redirect_ids)

    assert redirect_to_article == {10: 2, 11: 1, 15: 3}
    assert stats["target page missing"] == 1
    assert stats["point to another wiki"] == 1
    assert stats["double redirect"] == 1
    assert stats["target not in namespace 0"] == 1
    assert stats["not a ns-0 redirect page"] == 1


def test_resolve_linktargets(dumps):
    title_to_id, redirect_ids, _ = load_page_index(dumps["page"])
    redirect_to_article, _ = load_redirects(dumps["redirect"], title_to_id, redirect_ids)
    lt_to_article, stats = resolve_linktargets(
        dumps["linktarget"], title_to_id, redirect_ids, redirect_to_article
    )

    assert lt_to_article == {100: 2, 101: 2, 102: 1, 103: 1, 107: 3}
    assert stats["red link"] == 1
    assert stats["unusable redirect"] == 2
    assert stats["not namespace 0"] == 1


def test_build_edges_end_to_end(dumps, tmp_path):
    title_to_id, redirect_ids, _ = load_page_index(dumps["page"])
    redirect_to_article, _ = load_redirects(dumps["redirect"], title_to_id, redirect_ids)
    lt_to_article, _ = resolve_linktargets(
        dumps["linktarget"], title_to_id, redirect_ids, redirect_to_article
    )
    article_ids = {pid for pid in title_to_id.values() if pid not in redirect_ids}
    edges, stats = build_edges(dumps["pagelinks"], article_ids, redirect_ids, lt_to_article)

    assert list(zip(edges["source"].to_pylist(), edges["target"].to_pylist(), strict=True)) == [
        (1, 2),
        (1, 3),
        (2, 1),
        (2, 3),
    ]
    assert stats["duplicates removed"] == 1
    assert stats["self loop"] == 1
    assert stats["source is a redirect"] == 1
    assert stats["source not namespace 0"] == 1
    assert stats["source page unknown"] == 1

    # Write both files and read them back, the way the graph stage will.
    write_pages(title_to_id, redirect_ids, tmp_path / "pages.parquet")
    write_edges(edges, tmp_path / "edges.parquet")
    pages = pq.read_table(tmp_path / "pages.parquet")
    edges_back = pq.read_table(tmp_path / "edges.parquet")

    assert str(pages.schema) == "page_id: int64\ntitle: string"
    assert str(edges_back.schema) == "source: int64\ntarget: int64"
    assert pages["title"].to_pylist() == ["Munich", "Bavaria", "Germany", "Isar"]
    page_ids = set(pages["page_id"].to_pylist())
    assert set(edges_back["source"].to_pylist()) <= page_ids
    assert set(edges_back["target"].to_pylist()) <= page_ids
