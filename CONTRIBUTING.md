# How we work

## Branches

- `main` is protected: no direct pushes, everything goes through a pull request.
- One branch per task, named after its type:
  - `feature/dump-parser`
  - `fix/redirect-resolution`
  - `exp/landmark-heuristic` (experiments)

```bash
git switch main && git pull
git switch -c feature/my-task
# ...work, commit...
git push -u origin feature/my-task
# open a PR on GitHub, link the issue ("Closes #12")
```

## Pull requests

- Keep them small (ideally < 400 changed lines).
- The other person reviews before merging. Review within 24h if possible.
- CI (ruff + pytest) must be green.
- Merge with **Squash and merge**, then delete the branch.

## Commits

Short, imperative messages: `Add redirect resolution to parser`, not `stuff` or `fixed things`.

## Tasks

- Every task is a GitHub Issue, assigned to one person.
- The Project board shows status: To do → In progress → In review → Done.
- If you start something, move it to *In progress* so we don't both do it.

## Code

- Real logic goes in `src/wikigraph/`, not in notebooks.
- Formatting/linting is automatic via pre-commit (ruff). Don't fight it.
- New functionality gets at least one test in `tests/`.
- Never commit data files. `data/` is gitignored and pre-commit blocks files > 5 MB.

## Sync

- Weekly meeting (~20 min): what's done, what's next, blockers.
- Quick questions in chat.
