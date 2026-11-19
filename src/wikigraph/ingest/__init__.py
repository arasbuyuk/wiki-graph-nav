"""Stage 1: parse Wikipedia SQL dumps into a clean edge list.

Output contract (see README):
  data/processed/edges.parquet  columns: source int64, target int64
  data/processed/pages.parquet  columns: page_id int64, title string

TODO:
  - stream-parse INSERT statements from *.sql.gz (don't load whole files into memory)
  - keep namespace 0 (articles) only
  - join pagelinks.pl_target_id -> linktarget -> page to get target page_id
  - resolve redirects to their final target
  - drop self-loops and duplicate edges
"""
