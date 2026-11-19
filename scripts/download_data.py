"""Download the Wikipedia SQL dumps needed to build the link graph.

Tables:
  page        page_id, namespace, title, is_redirect
  pagelinks   pl_from (page_id) -> pl_target_id (linktarget id)
  linktarget  lt_id -> (namespace, title)   [pagelinks no longer stores titles directly]
  redirect    rd_from (page_id) -> target title

Usage:
  uv run python scripts/download_data.py                 # simplewiki (dev)
  uv run python scripts/download_data.py --wiki enwiki   # full English Wikipedia
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from tqdm import tqdm

BASE_URL = "https://dumps.wikimedia.org/{wiki}/{date}/{wiki}-{date}-{table}.sql.gz"
TABLES = ["page", "pagelinks", "linktarget", "redirect"]
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"skip (exists): {dest.name}")
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        with (
            open(tmp, "wb") as f,
            tqdm(total=total, unit="B", unit_scale=True, desc=dest.name) as bar,
        ):
            while chunk := resp.read(1 << 20):
                f.write(chunk)
                bar.update(len(chunk))
    tmp.rename(dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wiki", default="simplewiki", help="e.g. simplewiki, enwiki, dewiki")
    parser.add_argument("--date", default="latest", help="dump date like 20261101, or 'latest'")
    parser.add_argument("--tables", nargs="+", default=TABLES)
    args = parser.parse_args()

    out_dir = RAW_DIR / args.wiki / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    for table in args.tables:
        url = BASE_URL.format(wiki=args.wiki, date=args.date, table=table)
        download(url, out_dir / f"{table}.sql.gz")
    print(f"done -> {out_dir}")


if __name__ == "__main__":
    main()
