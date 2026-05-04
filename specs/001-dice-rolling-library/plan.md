# Implementation Plan: RNG Injection for Dice Rolling Library

**Branch**: `addRNGInjection` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/001-dice-rolling-library/spec.md`

## Summary

Add an optional `rng=None` parameter to `Dice.roll()` and the `roll()` convenience function, accepting any duck-typed object with a `random() -> float` method. The parameter propagates through the full call chain — including nested modifier dice — so a single seeded `rng` instance makes an entire `Dice.roll()` invocation reproducible. All existing callers are unaffected. The CLI gains a `--seed` flag for reproducible command-line rolls.

## Technical Context

**Language/Version**: Python 3.11.7 (runtime); supports 3.8–3.12  
**Primary Dependencies**: None (core); `pytest`, `black`, `isort`, `ruff` for dev  
**Storage**: N/A  
**Testing**: pytest + pytest-cov; TDD mandatory per constitution  
**Target Platform**: Cross-platform (Linux, macOS, Windows)  
**Project Type**: Library + CLI tools  
**Performance Goals**: <1ms simple rolls; <100ms CLI startup  
**Constraints**: Python 3.8+ compatible; zero external dependencies; backward-compatible (all callers with no `rng` arg unaffected)  
**Scale/Scope**: ~2,300 LOC across 8 modules; surgical change, no new modules required

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Library-First | ✅ Pass | `rng=` is a pure library-level enhancement; no new modules required |
| II. CLI Interface | ✅ Pass | `tools/roll.py` gains `--seed N` flag; JSON output includes seed when used |
| III. Test-First | ✅ Pass | New test file `tests/test_dice_rng.py` written before implementation |
| IV. Mathematical Precision | ✅ Pass | RNG injection enables SC-009 reproducibility; distribution unchanged |
| V. RPG System Fidelity | ✅ Pass | All mechanics (fudge, percentile, explode, reroll) propagate `rng` |
| VI. Observability | ✅ Pass | Debug logging notes custom RNG when in use |
| Zero external deps | ✅ Pass | Duck-typed protocol; no new imports required |
| Python 3.8+ compat | ✅ Pass | No 3.9+ syntax used |
| Backward compat | ✅ Pass | `rng=None` default; existing callers compile and behave identically |

**No violations. Proceeding.**

## Project Structure

### Documentation (this feature)

```text
specs/001-dice-rolling-library/
├── plan.md              ← This file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── api.md           ← Phase 1 output
└── tasks.md             ← Phase 2 output (created by /speckit.tasks, not here)
```

### Source Code (files touched by this feature)

```text
src/wyrdbound_dice/
├── __init__.py          ← Update roll() convenience function signature
├── dice.py              ← PRIMARY: Dice.roll, roll_with_precedence,
│                           _roll_original_method, _parse_with_precedence,
│                           _handle_goodflux_roll, _handle_badflux_roll,
│                           DiceRoller.roll_standard_die,
│                           DiceRoller.roll_fudge_die,
│                           DiceRoller.roll_percentile_die
└── roll_result.py       ← RollModifier.roll, RollResultSet.__init__

tools/
└── roll.py              ← Add --seed flag

tests/
├── test_dice_rng.py     ← NEW: all rng injection tests (written first)
└── [existing tests]     ← Unchanged; must continue to pass
```

**Structure Decision**: Single-project layout unchanged. No new modules. RNG support is a parameter threaded through the existing call chain via a private `_randint()` helper at the `DiceRoller` level.

## Complexity Tracking

No constitution violations to justify.
