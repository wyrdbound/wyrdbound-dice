# Tasks: RNG Injection for Dice Rolling Library

**Input**: Design documents from `specs/001-dice-rolling-library/`  
**Branch**: `addRNGInjection` | **Date**: 2026-05-03  
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/api.md ✅ | quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US8 per spec.md)
- Exact file paths required in all task descriptions
- **Constitution Rule — Test-First (NON-NEGOTIABLE)**: Within each phase, all test tasks MUST be written and confirmed failing before any implementation task in that phase begins

---

## Phase 1: Setup & Baseline

**Purpose**: Confirm a green baseline before any changes; create the dedicated test file.

- [ ] T001 Run `python -m pytest tests/ -v` and confirm all existing tests pass; record count as baseline
- [ ] T002 [P] Create `tests/test_dice_rng.py` with module docstring, imports (`random`, `unittest.mock.Mock`, `pytest`, `Dice`, `roll`, `RollResultSet`), and a reusable `seeded_rng` pytest fixture returning `random.Random(42)`

**Checkpoint**: Green baseline confirmed; test file ready.

---

## Phase 2: Foundational — Core RNG Infrastructure

**Purpose**: Add `_randint` helper and thread `rng=None` through the entire call chain in `dice.py` and `__init__.py`. All user story phases depend on this being complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Write all tests in this phase first and verify they fail, then implement.

### Tests for Phase 2 (write first — verify ALL fail before T007)

- [ ] T003 Write failing test `test_randint_fallback_uses_stdlib`: assert `_randint(None, 1, 6)` returns an `int` in `[1, 6]` over 100 iterations in `tests/test_dice_rng.py`
- [ ] T004 Write failing test `test_randint_calls_rng_random`: assert `_randint(mock_rng, 1, 6)` calls `mock_rng.random()` exactly once and returns `int` in `[1, 6]` in `tests/test_dice_rng.py`
- [ ] T005 [P] Write failing test `test_dice_roll_accepts_rng_none`: assert `Dice.roll("1d6", rng=None)` returns a `RollResultSet` without raising `TypeError` in `tests/test_dice_rng.py`
- [ ] T006 [P] Write failing test `test_dice_roll_accepts_rng_object`: assert `Dice.roll("1d6", rng=mock_rng)` calls `mock_rng.random()` at least once in `tests/test_dice_rng.py`

### Implementation for Phase 2

- [ ] T007 Add module-private `_randint(rng, a: int, b: int) -> int` helper above `class RollModifier` in `src/wyrdbound_dice/dice.py`: returns `random.randint(a, b)` when `rng is None`, else `int(rng.random() * (b - a + 1)) + a`
- [ ] T008 Add `rng=None` parameter to `DiceRoller.roll_standard_die(sides, rng=None)`, `DiceRoller.roll_fudge_die(rng=None)`, and `DiceRoller.roll_percentile_die(rng=None)`; replace every `random.randint(...)` call in those three methods with `_randint(rng, ...)` in `src/wyrdbound_dice/dice.py`
- [ ] T009 Add `rng=None` to `Dice.roll()`, `Dice.roll_with_precedence()`, `Dice._roll_original_method()`, and `Dice._parse_with_precedence()`; thread `rng` to every `DiceRoller.*` call site and to every `cls._roll_original_method` / `cls._parse_with_precedence` call site in `src/wyrdbound_dice/dice.py`
- [ ] T010 Add `rng=None` to `Dice._handle_goodflux_roll()` and `Dice._handle_badflux_roll()`; thread `rng` to `FluxDiceHandler.roll_flux(rng=None)` and to both `DiceRoller.roll_standard_die(6, rng)` calls inside `FluxDiceHandler.roll_flux` in `src/wyrdbound_dice/dice.py`
- [ ] T011 Add `rng=None` to `RollResultSet.__init__(results, modifiers=None, dice_class=None, rng=None)` and to `RollModifier.roll(dice_class, rng=None)`; update the modifier roll loop in `RollResultSet.__init__` to call `modifier.roll(dice_class, rng=rng)`, and update `RollModifier.roll()` to call `dice_class.roll(self.dice_expression, rng=rng)` in `src/wyrdbound_dice/dice.py`
- [ ] T012 Add `rng=None` to the `roll()` convenience function signature and pass it through to `Dice.roll()` in `src/wyrdbound_dice/__init__.py`; update the docstring to document the `rng` parameter
- [ ] T013 Add a debug log line `logger.log_step("RNG", f"Custom RNG in use: {type(rng).__name__}")` inside `Dice.roll()` when `rng is not None`, after the existing `[START]` log in `src/wyrdbound_dice/dice.py`
- [ ] T014 Run `python -m pytest tests/ -v` and confirm T003–T006 now pass and all prior baseline tests still pass

**Checkpoint**: Foundation complete — `_randint` helper live, full call chain accepts `rng=`. All user story phases can now proceed.

---

## Phase 3: US1–US5 — Standard Dice Seeding (Priority: P1–P5)

**Goal**: Prove that basic rolls, mathematical expressions, keep/drop, reroll, and exploding dice are all reproducible when a seeded `rng` is supplied. All five mechanics share `DiceRoller.roll_standard_die`, so they are verified together.

**Independent Test**: `python -c "import random; from wyrdbound_dice import Dice; rng=random.Random(42); r1=Dice.roll('4d6kh3',rng=rng); rng2=random.Random(42); r2=Dice.roll('4d6kh3',rng=rng2); assert r1.total==r2.total"`

### Tests for US1–US5 (write first — verify ALL fail before T019)

- [ ] T015 [P] [US1] Write failing test `test_basic_roll_reproducible`: two `Dice.roll("1d20", rng=random.Random(42))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T016 [P] [US1] Write failing test `test_mock_rng_pins_result`: `Dice.roll("1d6", rng=Mock(random=lambda: 0.9999)).total == 6` in `tests/test_dice_rng.py`
- [ ] T017 [P] [US3] Write failing test `test_keep_drop_reproducible`: two `Dice.roll("4d6kh3", rng=random.Random(7))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T018 [P] [US4] Write failing test `test_reroll_reproducible`: two `Dice.roll("2d6r<=2", rng=random.Random(7))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T019 [P] [US5] Write failing test `test_exploding_reproducible`: two `Dice.roll("1d6e", rng=random.Random(7))` calls produce equal totals in `tests/test_dice_rng.py`

### Verification for US1–US5

- [ ] T020 [US1] Run `python -m pytest tests/test_dice_rng.py::test_basic_roll_reproducible tests/test_dice_rng.py::test_mock_rng_pins_result tests/test_dice_rng.py::test_keep_drop_reproducible tests/test_dice_rng.py::test_reroll_reproducible tests/test_dice_rng.py::test_exploding_reproducible -v` and confirm all five pass with no new implementation required (Phase 2 covers these)

**Checkpoint**: Basic, math, keep/drop, reroll, and exploding dice all reproducible with seeded RNG.

---

## Phase 4: US6 — Fudge Dice Seeding (Priority: P6)

**Goal**: Prove that Fudge/Fate dice (`dF`) rolls are reproducible when a seeded `rng` is supplied.

**Independent Test**: `python -c "import random; from wyrdbound_dice import Dice; r1=Dice.roll('4dF',rng=random.Random(1)); r2=Dice.roll('4dF',rng=random.Random(1)); assert r1.total==r2.total"`

### Tests for US6 (write first — verify fail before T023)

- [ ] T021 [P] [US6] Write failing test `test_fudge_reproducible`: two `Dice.roll("4dF", rng=random.Random(1))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T022 [P] [US6] Write failing test `test_fudge_mock_min`: `Mock(random=lambda: 0.0)` always produces `-1` per fudge die; assert `Dice.roll("1dF", rng=mock).total == -1` in `tests/test_dice_rng.py`

### Verification for US6

- [ ] T023 [US6] Run `python -m pytest tests/test_dice_rng.py::test_fudge_reproducible tests/test_dice_rng.py::test_fudge_mock_min -v` and confirm both pass (DiceRoller.roll_fudge_die updated in Phase 2 T008)

**Checkpoint**: Fudge dice reproducible with seeded RNG.

---

## Phase 5: US7 — System Shorthands Seeding (Priority: P7)

**Goal**: Prove that GOODFLUX, BADFLUX, and percentile (`1d%`) shorthand rolls are reproducible when a seeded `rng` is supplied.

**Independent Test**: `python -c "import random; from wyrdbound_dice import Dice; r1=Dice.roll('GOODFLUX',rng=random.Random(5)); r2=Dice.roll('GOODFLUX',rng=random.Random(5)); assert r1.total==r2.total"`

### Tests for US7 (write first — verify fail before T027)

- [ ] T024 [P] [US7] Write failing test `test_goodflux_reproducible`: two `Dice.roll("GOODFLUX", rng=random.Random(5))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T025 [P] [US7] Write failing test `test_badflux_reproducible`: two `Dice.roll("BADFLUX", rng=random.Random(5))` calls produce equal totals in `tests/test_dice_rng.py`
- [ ] T026 [P] [US7] Write failing test `test_percentile_reproducible`: two `Dice.roll("1d%", rng=random.Random(3))` calls produce equal totals in `tests/test_dice_rng.py`

### Verification for US7

- [ ] T027 [US7] Run `python -m pytest tests/test_dice_rng.py::test_goodflux_reproducible tests/test_dice_rng.py::test_badflux_reproducible tests/test_dice_rng.py::test_percentile_reproducible -v` and confirm all three pass (Phase 2 T008–T010 covers these paths)

**Checkpoint**: GOODFLUX, BADFLUX, and percentile rolls all reproducible.

---

## Phase 6: US8 — Named Modifier Propagation (Priority: P8)

**Goal**: Prove that a single seeded `rng` controls both the base roll and any dice modifier expressions end-to-end (FR-027 / SC-009).

**Independent Test**: `python -c "import random; from wyrdbound_dice import Dice; r1=Dice.roll('1d20',modifiers={'Bless':'1d4'},rng=random.Random(9)); r2=Dice.roll('1d20',modifiers={'Bless':'1d4'},rng=random.Random(9)); assert r1.total==r2.total"`

### Tests for US8 (write first — verify fail before T030)

- [ ] T028 [P] [US8] Write failing test `test_modifier_propagation_reproducible`: two `Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=random.Random(9))` produce equal totals in `tests/test_dice_rng.py`
- [ ] T029 [P] [US8] Write failing test `test_modifier_mock_controls_all_dice`: with a `Mock` whose `random()` always returns `0.9999`, assert both the base d20 and the Bless 1d4 are at their maximums (20 and 4) in `tests/test_dice_rng.py`

### Verification for US8

- [ ] T030 [US8] Run `python -m pytest tests/test_dice_rng.py::test_modifier_propagation_reproducible tests/test_dice_rng.py::test_modifier_mock_controls_all_dice -v` and confirm both pass (Phase 2 T011 covers this path)

**Checkpoint**: Named modifier dice propagate the same `rng` — full call is end-to-end reproducible.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: CLI `--seed` flag, documentation updates, and full regression.

- [ ] T031 Add `--seed` integer argument to `tools/roll.py`; when provided, construct `random.Random(args.seed)` and pass as `rng=` to `Dice.roll()`; include `"seed": args.seed` in JSON output alongside `"result"` and `"description"` (for multi-roll JSON output, wrap results in `{"seed": N, "results": [...]}`)
- [ ] T032 [P] Update docstrings for `Dice.roll()`, `DiceRoller.roll_standard_die()`, `DiceRoller.roll_fudge_die()`, `DiceRoller.roll_percentile_die()`, and `RollModifier.roll()` to document the `rng` parameter in `src/wyrdbound_dice/dice.py`
- [ ] T033 [P] Update `README.md`: add "RNG Injection" section under Debug Logging; include seeded roll example, mock testing example, and `--seed` CLI example drawn from `specs/001-dice-rolling-library/quickstart.md`
- [ ] T034 [P] Add entry under `[Unreleased]` in `CHANGELOG.md`: `feat: Add rng= parameter to Dice.roll() for reproducible, testable dice rolling`
- [ ] T035 Run full test suite `python -m pytest tests/ -v --cov=wyrdbound_dice` and confirm all tests pass; run `black src/ tests/ tools/`, `isort src/ tests/ tools/`, `ruff check src/ tests/ tools/` and resolve any issues

**Checkpoint**: All tests green, linting clean, docs updated, CLI enhanced. Feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all US phases**
- **Phase 3–6 (User Stories)**: All depend on Phase 2; can run sequentially or in parallel after Phase 2
- **Phase 7 (Polish)**: Depends on Phases 3–6

### User Story Dependencies

- **US1–US5 (Phase 3)**: Can start immediately after Phase 2 — implementation already done in Phase 2; phase is test verification only
- **US6 (Phase 4)**: Can run in parallel with Phase 3 — independent verification path (fudge die)
- **US7 (Phase 5)**: Can run in parallel with Phases 3–4 — independent verification path (flux/percentile)
- **US8 (Phase 6)**: Can run in parallel with Phases 3–5 — independent propagation path (modifiers)

### Within Each Phase: Test-First Order

Per constitution (III. Test-First — NON-NEGOTIABLE):
1. Write all test tasks for the phase → confirm they ALL FAIL
2. Run implementation tasks
3. Confirm tests now pass
4. Run full baseline to confirm no regressions

### Critical Path

```
T001 → T002 → T003–T006 (fail confirmed) → T007–T013 → T014 (green)
                                                                ↓
                                          T015–T019 (fail) → T020 (green)
                                          T021–T022 (fail) → T023 (green)
                                          T024–T026 (fail) → T027 (green)
                                          T028–T029 (fail) → T030 (green)
                                                                ↓
                                                         T031–T035
```

---

## Parallel Opportunities

```bash
# Phase 1 — both tasks can run in parallel:
Task T001: Run baseline test suite
Task T002: Create tests/test_dice_rng.py

# Phase 2 test writing — all four can be written in parallel:
Task T003: test_randint_fallback_uses_stdlib
Task T004: test_randint_calls_rng_random
Task T005: test_dice_roll_accepts_rng_none
Task T006: test_dice_roll_accepts_rng_object

# Phase 3–6 verification — all can run in parallel once Phase 2 is done:
Task T015–T020: US1–US5 standard die tests
Task T021–T023: US6 fudge die tests
Task T024–T027: US7 shorthand tests
Task T028–T030: US8 modifier propagation tests

# Phase 7 — T032, T033, T034 can all run in parallel:
Task T032: Update docstrings
Task T033: Update README
Task T034: Update CHANGELOG
```

---

## Implementation Strategy

### MVP First (Phase 1 + 2 only — foundational complete)

1. Complete Phase 1: Baseline green
2. Complete Phase 2: `_randint` helper + full signature threading
3. **STOP and VALIDATE**: `Dice.roll("2d6", rng=random.Random(42))` is reproducible
4. All eight user stories already benefit — Phase 3–6 are verification, not new implementation

### Incremental Delivery

1. Phase 1 + 2 → Core injection works → **All mechanics already reproducible**
2. Phase 3 → Verified: basic, math, keep/drop, reroll, exploding
3. Phase 4 → Verified: fudge dice
4. Phase 5 → Verified: GOODFLUX, BADFLUX, percentile
5. Phase 6 → Verified: named modifier propagation
6. Phase 7 → CLI exposed, docs complete, release-ready

### Key Implementation Note

Because all dice rolling ultimately flows through three `DiceRoller` static methods (`roll_standard_die`, `roll_fudge_die`, `roll_percentile_die`), the entire feature is implemented in Phase 2 (T007–T013). Phases 3–6 are verification phases that confirm correct propagation through each path of the call tree. This means Phase 2 is the only phase with new code — all subsequent phases add tests only.

---

## Notes

- `[P]` tasks touch different files or independent sections — safe to run in parallel
- `[USn]` label maps task to spec.md user story for traceability
- Constitution III is enforced: every test in this list must be written and confirmed failing before its corresponding implementation task runs
- `RollModifier`, `RollResultSet`, `DiceRoller`, `FluxDiceHandler` are all defined in `src/wyrdbound_dice/dice.py` (not `roll_result.py`)
- Commit after each phase checkpoint using conventional commits (e.g., `feat: Add _randint helper and RNG parameter threading`, `test: Add RNG injection test coverage`)
