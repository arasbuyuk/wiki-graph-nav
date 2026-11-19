# Navigating the Wikipedia Link Graph

TUM Bachelor Practical Course: Data Engineering (WS 2026/27).

We model Wikipedia as a directed graph (article → linked article) and use
**A\* search** with custom heuristics to find short paths between two articles.

## Pipeline

| Stage | Package | Input → Output |
|---|---|---|
| 1. Ingestion | `wikigraph.ingest` | Wikipedia dumps → clean edge list (`data/processed/edges.parquet`) |
| 2. Graph | `wikigraph.graph` | edge list → in-memory graph (+ article ID ↔ title mapping) |
| 3. Search | `wikigraph.search` | graph + start/goal → path (A\*, baselines like BFS) |
| 4. Evaluation | `wikigraph.evaluation` | benchmark queries → metrics (path length, nodes expanded, runtime) |

**Interface contract between stages** (change only via PR + agreement):

- `edges.parquet`: columns `source: int64`, `target: int64` (page IDs)
- `pages.parquet`: columns `page_id: int64`, `title: string`

## Setup

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

```bash
git clone <repo-url>
cd wiki-graph-nav
uv sync                      # creates .venv and installs everything
uv run pre-commit install    # enables formatting/safety checks on every commit
uv run pytest                # should pass
```

## Getting the data

Data is **never committed** – everyone downloads it locally:

```bash
uv run python scripts/download_data.py              # simplewiki (small, for development)
uv run python scripts/download_data.py --wiki enwiki   # full English Wikipedia (many GB)
```

Files land in `data/raw/`. Develop on `simplewiki`, run final experiments on `enwiki`.

## Project structure

```
src/wikigraph/      # all real code (importable package)
  ingest/  graph/  search/  evaluation/
scripts/            # CLI entry points (download, preprocess, run benchmarks)
notebooks/          # exploration only – move finished logic into src/
tests/              # pytest
data/               # local only, gitignored
```

## How we work

See [CONTRIBUTING.md](CONTRIBUTING.md).
