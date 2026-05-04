# Tasks: RNG Injection for Dice Rolling Library

**Input**: Design documents from `specs/001-dice-rolling-library/`  
**Branch**: `addRNGInjection` | **Date**: 2026-05-03  
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/api.md ✅ | quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — requires **different files** and no dependency on incomplete tasks
- **[Story]**: Which user story this task belongs to (US1–US8 per spec.md)
- Exact file paths required in all task descriptions
- **Constitution Rule — Test-First (NON-NEGOTIABLE)**: ALL tests (T003–T019) MUST be written and confirmed failing before the first implementation task (T020) begins

---

## Phase 1: Setup & Baseline

**Purpose**: Confirm a green baseline before any changes; create the dedicated test file.

- [ ] T001 Run `python -m pytest tests/ -v` and confirm all existing tests pass; note the passing count in a comment at the top of the soon-to-be-created `tests/test_dice_rng.py`
- [ ] T002 [P] Create `tests/test_dice_rng.py` with module docstring, imports (`import random`, `from unittest.mock import Mock`, `import pytest`, `from wyrdbound_dice import Dice, roll, RollResultSet`, `from wyrdbound_dice.dice import _randint`), and a reusable `seeded_rng` pytest fixture returning `random.Random(42)`

**Checkpoint**: Green baseline confirmed; test file scaffolding ready.

---

## Phase 2: Foundational — All Tests First, Then Implementation

**Purpose**: Thread `rng=None` through the entire call chain. This phase follows a strict three-step TDD sequence: **(A) write all failing tests → (B) implement → (C) verify green**. No implementation begins until every test in Step A is confirmed failing.

---

### Step A: Write All Failing Tests

> ⛔ **Write T003–T019 in order. After T019, run the full test file and confirm every new test FAILS before proceeding to T020.**

Note: T003–T019 all write functions into `tests/test_dice_rng.py` and are therefore sequential — not parallelisable.

#### Infrastructure Tests

- [ ] T003 Write failing test `test_randint_fallback_uses_stdlib`: import `_randint` via `from wyrdbound_dice.dice import _randint`; assert `_randint(None, 1, 6)` returns an `int` in `[1, 6]` over 100 iterations in `tests/test_dice_rng.py`
- [ ] T004 Write failing test `test_randint_calls_rng_random`: import `_randint` via `from wyrdbound_dice.dice import _randint`; assert `_randint(mock_rng, 1, 6)` calls `mock_rng.random()` exactly once and returns an `int` in `[1, 6]` in `tests/test_dice_rng.py`

#### US1 — Basic Dice Rolling

- [ ] T005 [US1] Write failing test `test_dice_roll_accepts_rng_none`: assert `Dice.roll("1d6", rng=None)` returns a `RollResultSet` without raising `TypeError` in `tests/test_dice_rng.py`
- [ ] T006 [US1] Write failing test `test_dice_roll_uses_rng_random`: assert `Dice.roll("1d6", rng=mock_rng)` calls `mock_rng.random()` at least once in `tests/test_dice_rng.py`
- [ ] T007 [US1] Write failing test `test_basic_roll_reproducible`: two `Dice.roll("1d20", rng=random.Random(42))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T008 [US1] Write failing test `test_mock_rng_pins_result`: `Dice.roll("1d6", rng=Mock(random=lambda: 0.9999)).total == 6` in `tests/test_dice_rng.py`

#### US2 — Mathematical Operations (Precedence Parser Path)

- [ ] T009 [US2] Write failing test `test_precedence_parser_reproducible`: two `Dice.roll("2d6 + 1d4 × 2", rng=random.Random(42))` calls produce equal totals in `tests/test_dice_rng.py`; this expression forces the `_parse_with_precedence` code path

#### US3 — Keep/Drop Mechanics

- [ ] T010 [US3] Write failing test `test_keep_drop_reproducible`: two `Dice.roll("4d6kh3", rng=random.Random(7))` calls produce equal totals in `tests/test_dice_rng.py`

#### US4 — Reroll Mechanics

- [ ] T011 [US4] Write failing test `test_reroll_reproducible`: two `Dice.roll("2d6r<=2", rng=random.Random(7))` calls produce equal totals in `tests/test_dice_rng.py`

#### US5 — Exploding Dice

- [ ] T012 [US5] Write failing test `test_exploding_reproducible`: two `Dice.roll("1d6e", rng=random.Random(7))` calls produce equal totals in `tests/test_dice_rng.py`

#### US6 — Fudge Dice

- [ ] T013 [US6] Write failing test `test_fudge_reproducible`: two `Dice.roll("4dF", rng=random.Random(1))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T014 [US6] Write failing test `test_fudge_mock_min`: with `Mock(random=lambda: 0.0)`, assert `Dice.roll("1dF", rng=mock).total == -1` in `tests/test_dice_rng.py`

#### US7 — System Shorthands

- [ ] T015 [US7] Write failing test `test_goodflux_reproducible`: two `Dice.roll("GOODFLUX", rng=random.Random(5))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T016 [US7] Write failing test `test_badflux_reproducible`: two `Dice.roll("BADFLUX", rng=random.Random(5))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T017 [US7] Write failing test `test_percentile_reproducible`: two `Dice.roll("1d%", rng=random.Random(3))` calls produce equal totals in `tests/test_dice_rng.py`

#### US8 — Named Modifier Propagation

- [ ] T018 [US8] Write failing test `test_modifier_propagation_reproducible`: two `Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=random.Random(9))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T019 [US8] Write failing test `test_modifier_mock_controls_all_dice`: with `Mock(random=lambda: 0.9999)`, assert `Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=mock).total == 24` (20 + 4) in `tests/test_dice_rng.py`

> ⛔ **GATE**: Run `python -m pytest tests/test_dice_rng.py -v` now. Confirm T003–T019 ALL fail (NameError or TypeError expected). Do not proceed to T020 until every test in this file fails.

---

### Step B: Implementation

- [ ] T020 Add module-private `_randint(rng, a: int, b: int) -> int` helper above `class RollModifier` in `src/wyrdbound_dice/dice.py`: returns `random.randint(a, b)` when `rng is None`, else `int(rng.random() * (b - a + 1)) + a`
- [ ] T021 Add `rng=None` parameter to `DiceRoller.roll_standard_die(sides, rng=None)`, `DiceRoller.roll_fudge_die(rng=None)`, and `DiceRoller.roll_percentile_die(rng=None)`; replace every `random.randint(...)` call in those three methods with `_randint(rng, ...)` in `src/wyrdbound_dice/dice.py`
- [ ] T022 Add `rng=None` to `Dice.roll()`, `Dice.roll_with_precedence()`, `Dice._roll_original_method()`, and `Dice._parse_with_precedence()`; thread `rng` to every `DiceRoller.*` call site and to every `cls._roll_original_method` / `cls._parse_with_precedence` call site in `src/wyrdbound_dice/dice.py`
- [ ] T023 Add `rng=None` to `Dice._handle_goodflux_roll()` and `Dice._handle_badflux_roll()`; thread `rng` to `FluxDiceHandler.roll_flux(rng=None)` and to both `DiceRoller.roll_standard_die(6, rng)` calls inside `FluxDiceHandler.roll_flux` in `src/wyrdbound_dice/dice.py`
- [ ] T024 Add `rng=None` to `RollResultSet.__init__(results, modifiers=None, dice_class=None, rng=None)` and to `RollModifier.roll(dice_class, rng=None)`; update the modifier roll loop in `RollResultSet.__init__` to call `modifier.roll(dice_class, rng=rng)`, and update `RollModifier.roll()` to call `dice_class.roll(self.dice_expression, rng=rng)` in `src/wyrdbound_dice/dice.py`
- [ ] T025 Add `rng=None` to the `roll()` convenience function signature and pass it through to `Dice.roll()` in `src/wyrdbound_dice/__init__.py`; update the docstring to document the `rng` parameter
- [ ] T026 Add debug log line `logger.log_step("RNG", f"Custom RNG in use: {type(rng).__name__}")` inside `Dice.roll()` when `rng is not None`, immediately after the existing `[START]` log in `src/wyrdbound_dice/dice.py`

---

### Step C: Verify Green

- [ ] T027 Run `python -m pytest tests/test_dice_rng.py -v` and confirm all T003–T019 now pass; then run `python -m pytest tests/ -v` and confirm all prior baseline tests still pass with no regressions

**Checkpoint**: Foundation complete — all mechanics reproducible with seeded RNG. Red→Green cycle satisfied for all user stories.

---

## Phase 3: Polish & Cross-Cutting Concerns

**Purpose**: CLI `--seed` flag, concurrent safety verification, documentation, and final regression.

- [ ] T028 Add `--seed` integer argument to `tools/roll.py`; when provided, construct `random.Random(args.seed)` and pass as `rng=` to `Dice.roll()`; for single-roll JSON include `"seed": args.seed` alongside `"result"` and `"description"`; for multi-roll JSON (`--count N`) wrap results in `{"seed": N, "results": [...]}`
- [ ] T029 [P] Update docstrings for `Dice.roll()`, `DiceRoller.roll_standard_die()`, `DiceRoller.roll_fudge_die()`, `DiceRoller.roll_percentile_die()`, and `RollModifier.roll()` to document the `rng` parameter in `src/wyrdbound_dice/dice.py`
- [ ] T030 [P] Update `README.md`: add "RNG Injection" subsection under Debug Logging with a seeded roll example, a mock testing example, and the `--seed` CLI example from `specs/001-dice-rolling-library/quickstart.md`
- [ ] T031 [P] Add entry under `[Unreleased]` in `CHANGELOG.md`: `feat: Add rng= parameter to Dice.roll() for reproducible, testable dice rolling`
- [ ] T032 Write failing test `test_concurrent_rng_safety` in `tests/test_dice_rng.py`: use `concurrent.futures.ThreadPoolExecutor(max_workers=20)` to submit 1000 calls of `Dice.roll("2d6", rng=random.Random(i))` each with a unique per-thread seed `i`; assert all 1000 results are `RollResultSet` instances with `.total` in `[2, 12]` and that no exceptions were raised — verifying SC-006 with the new rng parameter
- [ ] T033 Run `python -m pytest tests/ -v --cov=wyrdbound_dice` and confirm all tests pass; then run `black src/ tests/ tools/`, `isort src/ tests/ tools/`, `ruff check src/ tests/ tools/` and resolve any issues before committing

**Checkpoint**: All tests green, linting clean, docs updated, CLI enhanced, thread safety verified. Feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (T001–T002)**: No dependencies — start immediately
- **Phase 2 Step A (T003–T019)**: Depends on Phase 1 — sequential, all write to `tests/test_dice_rng.py`
- **Phase 2 Step B (T020–T026)**: BLOCKED until all T003–T019 confirmed failing — sequential, dependent chain in `dice.py`
- **Phase 2 Step C (T027)**: Depends on T020–T026 completion
- **Phase 3 (T028–T033)**: Depends on T027 — T029, T030, T031 can run in parallel (different files)

### Critical Path

```
T001 ─┐
       ├─► T002 ─► T003 ─► T004 ─► ... ─► T019
       │                                      │
       │              ⛔ GATE (all fail)        │
       │                                      ▼
       │                         T020 ─► T021 ─► T022 ─► T023 ─► T024 ─► T025 ─► T026
       │                                                                              │
       │                                                                             T027
       │                                                                              │
       └─────────────────────────────────────────────────────────────────────────────►┤
                                                                                      │
                         T028 ─► T029 ─┐                                             │
                                  T030 ─┤ (parallel) ─► T032 ─► T033 ◄──────────────┘
                                  T031 ─┘
```

### [P] Justification

| Task | [P]? | Reason |
|------|------|--------|
| T002 | ✅ | Creates new file; T001 only reads |
| T003–T019 | ❌ | All append to same file `tests/test_dice_rng.py` |
| T020–T026 | ❌ | Sequential dependent chain in `dice.py` |
| T029 | ✅ | `src/wyrdbound_dice/dice.py` docstrings only |
| T030 | ✅ | `README.md` — different file from T029, T031 |
| T031 | ✅ | `CHANGELOG.md` — different file from T029, T030 |

---

## Parallel Opportunities

```bash
# Phase 1 — T001 and T002 can run concurrently:
Task T001: Run baseline test suite
Task T002: Create tests/test_dice_rng.py scaffolding

# Phase 3 — T029, T030, T031 can run concurrently:
Task T029: Update docstrings in dice.py
Task T030: Update README.md
Task T031: Update CHANGELOG.md
```

---

## Implementation Strategy

### MVP First (Phase 1 + 2 only)

1. Complete Phase 1: Green baseline
2. Complete Phase 2 Step A: All tests written and FAILING
3. Complete Phase 2 Step B: Implementation — rng threaded through
4. Complete Phase 2 Step C: All tests GREEN
5. **STOP and VALIDATE**: `Dice.roll("2d6", rng=random.Random(42))` is reproducible end-to-end

All eight user stories are verified in Phase 2. Phase 3 adds CLI exposure and polish only.

### Incremental Delivery

1. Phase 1 + 2 → Core injection complete for all mechanics (MVP)
2. Phase 3 → CLI `--seed`, concurrent safety confirmed, docs updated → release-ready

### Key Structural Note

Because all dice rolling flows through three `DiceRoller` static methods (`roll_standard_die`, `roll_fudge_die`, `roll_percentile_die`), the entire feature is implemented in Phase 2 Step B (T020–T026). Phase 2 Step A (T003–T019) is the TDD test suite written first. No implementation appears outside Phase 2 Step B and T028.

---

## Notes

- `[P]` = different files, no incomplete dependencies — 4 tasks qualify (T002, T029, T030, T031)
- `[USn]` label maps task to spec.md user story for traceability; US2 explicitly covered by T009
- Constitution §III enforced: GATE between T019 and T020 is mandatory — do not skip
- Constitution §III chaos engineering enforced: T032 covers SC-006 (1000+ concurrent)
- `RollModifier`, `RollResultSet`, `DiceRoller`, `FluxDiceHandler` are all defined in `src/wyrdbound_dice/dice.py`
- Conventional commits per constitution: e.g., `test: Add RNG injection test suite`, `feat: Thread rng parameter through dice rolling call chain`, `feat: Add --seed flag to CLI roll tool`
