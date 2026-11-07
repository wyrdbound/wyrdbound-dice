# wyrdbound-dice — Feature Index

Features come from the roadmap in [`../scope.md`](../scope.md), in its order.
[Questgiver](https://github.com/wyrdbound) plans each one and builds it one task
at a time, in a container, on a `feature/<key>-<slug>` branch.

Each feature is **two files**, named by its roadmap key:

- `<key>-<slug>.md` — the feature file: why it exists, its behavior (B1, B2, …),
  what is deliberately not in it, its acceptance script, its gate, and the
  clarifications made while planning. Written for a person.
- `<key>-<slug>-tasks.md` — the tasks file: 5 to 15 tasks, each naming its files,
  the rule it implements, and a runnable `*Accept:*` command. Written to be run
  **one task at a time by a coding agent that does not hold the feature file in
  context**.

Both follow Questgiver's plan format, which its format check enforces when a plan
is submitted. A tasks file waits for Justin's approval; Questgiver adds its
`**Approved:**` line when he gives it.

Completed features move to `done/`, both files together.

Older plans predate this format and are shipped documentation; leave them as they
are: feature 001 (`001-dice-rolling-library/`, the Spec Kit layout) and the
unkeyed two-file plans in `done/`.

The rules below are **binding on every task**.

---

## Rules for every task

1. **One task at a time.** Finish the current task, with its `*Accept:*` check and
   the tests for the files you changed green, and commit it, before the next.
2. **Do the task, and what it needs.** A task's `Files:` say where its work is
   expected, not a fence. Change another file when the task needs it, and name
   each such file, and why, in the commit body. Leave unrelated improvements
   alone.
3. **Do not add dependencies.** The core package is dependency-free (Article I).
   If you think you need one, stop and ask.
4. **The gate runs from the repo root**: `uv run --extra dev pytest`,
   `uv run --extra dev ruff check src/ tests/ tools/`, and
   `uv run --extra dev black --check src/ tests/ tools/` and
   `uv run --extra dev isort --check-only src/ tests/ tools/` reporting nothing
   to change. Line length 88 for `black`, 100 for `ruff`. Imports at the top of
   the file, always.
5. **Never invent file paths.** Use exactly the paths given, and for a file the
   task doesn't name, the existing layout.
6. **Never delete or weaken a passing test** to make a task pass. `AGENTS.md`
   Verification Contract §4.
7. **If a task is ambiguous, stop and ask** rather than guessing. In a Questgiver
   lane, run `questgiver ask "<question>"` and end the turn.
8. **Forward references are notes, not dependencies.** Tasks sometimes mention a
   later task. Those are orientation, and the current task is always completable
   without the later one. A forward reference you genuinely *cannot* satisfy is
   a **bug in the plan, not a choice for you to make**: stop and say so.
9. **Python 3.12 is the floor** for everything under `src/`. Builtin generics
   (`list[int]`), `X | None` unions and other 3.12 syntax are allowed; existing
   `typing.Optional`/`Tuple`/`Union` annotations are not rewritten unless a task
   says so.
10. **Bump the version once per feature**, in its last task, in `pyproject.toml`
    **and** `src/wyrdbound_dice/__init__.py:__version__`, keeping the two in
    sync. Semantic versioning; the feature file says which part moves.
11. **One commit per task**: `<type>(<key>): <task id> — <summary>`, for example
    `feat(V01): T003 — count successes in a dice pool`. The type is one of
    `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`, `build` or
    `style`; the summary starts lowercase and carries no itemized bullet list.
    The body says how each `*Accept:*` item was verified.
12. **Never tick a task's box.** Questgiver checks a task off after its own check
    passes.

---

## Definition of done for a feature

Its last task, additionally:

- `uv run --extra dev pytest --cov=wyrdbound_dice` passes.
- Docstrings exist on every public class, method and function the feature added.
- `README.md` is updated for any user-facing change, and `CHANGELOG.md` has an
  entry under `[Unreleased]`.
- The version is bumped in both places named in rule 10.

---

## Governance

`planning/constitution.md` — Articles I–VI — is binding on every task here, and
`AGENTS.md` summarises it. Where a tasks file and this README disagree, this
README's rules win for *how* to run the task; the constitution wins for *what*
the code must be.

---

## Completed features

| Feature | Design | Tasks | Released |
| --- | --- | --- | --- |
| Roll formatting | [`done/roll-formatting.md`](done/roll-formatting.md) | [`done/roll-formatting-tasks.md`](done/roll-formatting-tasks.md) | v0.1.0 |
| Expression validation | [`done/expression-validation.md`](done/expression-validation.md) | [`done/expression-validation-tasks.md`](done/expression-validation-tasks.md) | v0.3.0 |
