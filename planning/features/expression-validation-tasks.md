# Expression Validation — tasks

**Status:** In progress — Phase 2.
**Source design:** `planning/features/expression-validation.md` (§N references
below are into that document). `planning/features/README.md` — the global rules
for the executing agent — is binding on every task here.
**Scope:** fix multi-digit dice-count lexing; one pre-flight shared by `roll()`
and a new `validate()`; no fallback; `--check` on the CLI.

### Per-task definition of done

1. The named files exist with the described content, and nothing else changed.
2. `black --check src/ tests/ tools/`, `isort --check-only src/ tests/ tools/`
   and `ruff check src/ tests/ tools/` pass.
3. `python -m pytest tests/ -q` passes — except that a TDD test task is done
   when its new tests **fail for the stated reason** and every other test
   passes.
4. `python -m pytest tests/test_format_snapshots.py -q` is green after every
   task: output for valid expressions must not change (§3).
5. The task's box is ticked in the same commit.

---

## Phase 1 — Multi-digit dice counts (§1a)

- [x] **T001** Write `tests/test_multi_digit_dice_counts.py` (TDD). With an rng
  whose `random()` returns `0.5` (every d6 shows 4), assert
  `10d6 - 10d6 == 0`, `10d6 + 3 == 43`, `12d6 - 2 == 46` and
  `100d6 + 1d6 == 404`; and that `ExpressionLexer("10d6")` yields a single
  `DICE` token `"10d6"`.
  *Gate:* the arithmetic tests fail with wrong totals (80, 40, …).

- [x] **T002** In `src/wyrdbound_dice/expression_lexer.py`, make
  `_handle_digit_token` treat a run of digits followed by `d` as a dice term,
  whatever the number of digits — not only when the character after the first
  digit is `d`.
  *Accept:* T001 passes; the full suite passes.

## Phase 2 — One grammar for every expression (§1b, §1c, §3)

- [x] **T003** Write `tests/test_expression_rejection.py` (TDD). `Dice.roll`
  raises `ParseError` for each of `2d6 banana`, `1d20+{{ x }}`, `2d6+3 # note`,
  `1d6 + 1d6 + zz`, `3d6 5d8` (D1), `GOODFLUX + 3` and `GOODFLUX banana`.
  `GOODFLUX`, `BADFLUX` and `3d6 + 5d8` still roll.
  *Gate:* the rejection cases fail with "DID NOT RAISE".

- [ ] **T004** In `src/wyrdbound_dice/dice.py`, extract every check at the top
  of `_roll_single_dice_expression` that needs no die result — count and size
  limits, fudge-with-reroll, the infinite reroll/explode conditions, keep/drop
  parsing — into a classmethod `_parse_dice_term(expr, match)` returning the
  parsed parameters. `_roll_single_dice_expression` calls it, then rolls. A
  pure refactor: debug log lines keep their order.
  *Accept:* the suite passes unchanged (T003 still failing).

- [ ] **T005** In `src/wyrdbound_dice/dice.py` (and
  `src/wyrdbound_dice/expression_lexer.py` if the grammar gate needs the lexer
  to accept a form the original method accepts), add the pre-flight of §3 as
  `Dice._preflight(expr)`: steps 1–6, raising on the first failure. A flux
  shorthand must be the whole expression. Every DICE token must be matched by
  `_dice_re` in full. `roll_with_precedence` runs the pre-flight, then
  evaluates by today's path; remove the `except … _roll_original_method`
  fallback (D2).
  *Accept:* T003 passes; the full suite, including the format snapshots,
  passes.

**Checkpoint 1.** `python -m pytest tests/ -q --cov=wyrdbound_dice` passes.

## Phase 3 — `validate()` (§4)

- [ ] **T006** Write `tests/test_validate.py` (TDD). `Dice.validate` and
  `wyrdbound_dice.validate` return `None` for a corpus of valid expressions
  covering keep/drop, rerolls (`1d8r<5`), explosions, fudge, percentile,
  shorthands and arithmetic; raise the same exception type as `Dice.roll` for
  the T003 cases and for `1d6r<=6` (`InfiniteConditionError`); and never draw
  randomness — patch `random.random` and `random.randint` to raise, and
  validate the whole corpus.
  *Gate:* fails with `AttributeError` (no `validate`).

- [ ] **T007** Add `Dice.validate(expr) -> None` in
  `src/wyrdbound_dice/dice.py` — the pre-flight and nothing else — and a
  module-level `validate` in `src/wyrdbound_dice/__init__.py`, exported beside
  `roll`. Docstrings state the contract of §4, including that
  `DivisionByZeroError` is a rolling error.
  *Accept:* T006 passes.

- [ ] **T008** Add `--check` to `tools/roll.py` (Article II): validate instead
  of rolling; text output `valid` / exit 0, or the error on stderr / exit 1;
  under `--json`, `{"valid": true}` or `{"valid": false, "error": "…"}`. Add
  tests to `tests/test_cli_format.py` for both outcomes in both modes.
  *Accept:* the new CLI tests pass.

**Checkpoint 2.** Coverage run passes.

## Phase 4 — Release

- [ ] **T009** `README.md`: a "Validating expressions" section (§4), and a note
  under the expression syntax that whitespace-separated dice need an operator
  (D1). `CHANGELOG.md` under `[Unreleased]`: Added (`validate`, `--check`),
  Fixed (§1a totals, §1b silent acceptance, §1c flux), and the D1 behaviour
  change. Bump to `0.2.0` in `pyproject.toml` and `__init__.py:__version__`
  (D4). Set this list's status to Complete and list the feature as active in
  `planning/features/README.md`.
  *Accept:* the full gate passes.
