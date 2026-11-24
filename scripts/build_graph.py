"""Build pages.parquet and edges.parquet from the raw Wikipedia dump files."""

from collections import Counter
from pathlib import Path

from wikigraph.ingest.build import load_page_index, load_redirects, resolve_linktargets, write_pages

RAW = Path("data/raw/simplewiki/latest")
OUT = Path("data/processed/simplewiki")


def print_stats(name: str, stats: Counter) -> None:
    print(f"\n{name}")
    for key, value in stats.items():
        print(f"  {key:28} {value:>12,}")


def main() -> None:
    title_to_id, redirect_ids, page_stats = load_page_index(RAW / "page.sql.gz")
    print_stats("page", page_stats)
    n_pages = write_pages(title_to_id, redirect_ids, OUT / "pages.parquet")
    print(f"  -> wrote {n_pages:,} articles to {OUT / 'pages.parquet'}")

    redirect_to_article, redirect_stats = load_redirects(
        RAW / "redirect.sql.gz", title_to_id, redirect_ids
    )
    print_stats("redirect", redirect_stats)

    lt_to_article, lt_stats = resolve_linktargets(
        RAW / "linktarget.sql.gz", title_to_id, redirect_ids, redirect_to_article
    )
    print_stats("linktarget", lt_stats)


if __name__ == "__main__":
    main()
