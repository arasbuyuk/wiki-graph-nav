#!/usr/bin/env bash
# Creates labels and the first set of issues on GitHub.
# Requires the GitHub CLI (https://cli.github.com) and `gh auth login`.
# Run once from the repo root:  bash scripts/create_issues.sh
set -euo pipefail

label() { gh label create "$1" --color "$2" --force >/dev/null; }
label "stage: ingest"     "1f77b4"
label "stage: graph"      "2ca02c"
label "stage: search"     "d62728"
label "stage: evaluation" "9467bd"
label "infra"             "7f7f7f"
label "report"            "e377c2"

issue() { gh issue create --title "$1" --label "$2" --body "$3" >/dev/null && echo "created: $1"; }

issue "Set up repo, branch protection and project board" "infra" \
"- [ ] Both members have push access
- [ ] Branch protection on main (PR + 1 approval + CI)
- [ ] GitHub Project board with columns To do / In progress / In review / Done
- [ ] Both ran uv sync, pre-commit install, pytest locally"

issue "Explore simplewiki dumps" "stage: ingest" \
"Download simplewiki with scripts/download_data.py and explore page, pagelinks, linktarget, redirect in a notebook.
Note sizes, row counts, namespaces and anything surprising."

issue "Stream parser for SQL dumps" "stage: ingest" \
"Parse INSERT rows from *.sql.gz without loading the whole file into memory. Must scale to enwiki."

issue "Build edge list: links + linktarget + redirects" "stage: ingest" \
"Produce data/processed/edges.parquet and pages.parquet (see README contract).
Namespace 0 only, redirects resolved, no self-loops or duplicates."

issue "Choose and implement graph representation" "stage: graph" \
"Compare options (e.g. numpy CSR vs graph library) on load time and memory for simplewiki and enwiki. Document the decision."

issue "BFS baseline" "stage: search" \
"Shortest path in hops. Serves as ground truth for evaluating A*."

issue "Generic A* with pluggable heuristic" "stage: search" \
"A* that takes a heuristic function; test on small hand-made graphs first."

issue "Research heuristics for A* on Wikipedia" "stage: search" \
"Collect candidates (landmarks/ALT, embeddings, category overlap, ...), note admissibility and cost. Pick 2-3 to implement."

issue "Benchmark harness" "stage: evaluation" \
"Reproducible query set (fixed seed), metrics: path length vs BFS, nodes expanded, runtime. Output CSV in results/."

issue "Clarify course deliverables and deadlines" "report" \
"Collect milestones, report/presentation requirements and grading criteria from the course page. Add them as GitHub milestones."
