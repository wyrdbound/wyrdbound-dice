# wyrdbound-dice — Feature Index

This directory holds feature work as **two files per feature**:

- `<slug>.md` — the design document. What the problem is, what already exists,
  the model, what must be fixed to ship, what was deliberately left out, and the
  decisions taken. Written to be read once, by a person.
- `<slug>-tasks.md` — the execution list. Written to be run **one task at a time,
  in order, by a coding agent that does not hold the design document in
  context**. Every task names its files, restates the rule it implements, and
  states its own acceptance check. Do not read ahead; do not batch.

Completed features move to `done/`, both files together.

Feature 001 (`001-dice-rolling-library/`) predates this convention and uses the
older Spec Kit directory layout. It is shipped documentation; leave it as it is.
New features use the two-file form.

The rules below are **binding on every task in every list in this directory**.
They keep each task small and committed, so a long build does not burn a session
re-fixing lint at the end.

---

## Global rules for the executing agent

1. **Do exactly one task per run.** Do not start the next task until the current
   one is committed.
2. **Do not refactor code outside the task's listed files.** Stage only the files
   that task created or changed.
3. **Do not add dependencies.** The core package is dependency-free (Article I).
   If you think you need one, stop and ask.
4. **The gate runs from the repo root**: `python -m pytest tests/ -q` and
   `ruff check src/ tests/ tools/`, with `black src/ tests/ tools/` and
   `isort src/ tests/ tools/` producing no diff. Line length 88 for `black`,
   100 for `ruff`. Imports at the top of the file, always.
5. **Every task must end with its verification command passing.** If it fails,
   fix it before finishing. The per-task definition of done in each list names
   the exact commands.
6. **Never invent file paths.** Use exactly the paths given.
7. **Never delete or weaken a passing test** to make a task pass. `AGENTS.md`
   Verification Contract §4.
8. **If a task is ambiguous, stop and ask** rather than guessing. `AGENTS.md`
   General Working Principle 7.
9. **Forward references are notes, not dependencies.** Tasks sometimes mention a
   later task — "lands in T059", "T068 switches this". Those are orientation, and
   the current task is always completable without the later one. If you find a
   forward reference you genuinely *cannot* satisfy, that is a **bug in the plan,
   not a choice for you to make**. Stop and say so; do not pull the later task
   forward, and do not weaken the acceptance criteria to compensate.
10. **Python 3.8 is the floor** for everything under `src/`. `typing.Tuple`,
    `typing.Optional`, `typing.Union` — no builtin generics, no `X | Y` unions,
    no `dataclasses(slots=True)`.
11. **Bump the version** in `pyproject.toml` **and**
    `src/wyrdbound_dice/__init__.py:__version__` when a task changes behaviour,
    keeping the two in sync. Semantic versioning; each list states its own
    per-checkpoint bump policy.
12. **Commit after each task, then continue.** Once a task passes its
    verification, commit it with a Conventional Commits message — `feat`, `fix`,
    `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build`, `style`, with the
    description starting lowercase and carrying no itemized bullet list. Stage
    only the files that task created or changed. **Never bundle two tasks into
    one commit.** In that same commit, tick the task's box `[x]` in the list so
    later agents can see what is done.

---

## Per-phase definition of done

At each **Checkpoint** in a list, additionally:

- `python -m pytest tests/ -q --cov=wyrdbound_dice` passes.
- `black`, `isort` and `ruff` are clean across `src/ tests/ tools/`.
- Docstrings exist on every public class, method and function added in the phase.
- `README.md` is updated for any user-facing change, and `CHANGELOG.md` has an
  entry under `[Unreleased]`.
- The version is bumped in both places named in rule 11.

---

## Governance

`planning/constitution.md` — Articles I–VI — is binding on every task in every
list here, and `AGENTS.md` summarises it. Where a task file and this README
disagree, this README's execution rules win for *how* to run the list; the
constitution wins for *what* the code must be.

---

## Active features

| Feature | Design | Tasks | Status |
| --- | --- | --- | --- |
| Roll formatting | [`roll-formatting.md`](roll-formatting.md) | [`roll-formatting-tasks.md`](roll-formatting-tasks.md) | In progress. Phase 4 done; Phase 5 next. |
