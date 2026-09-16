# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `--format {standard,compact,minimal,verbose}` and `--detail` flags on `tools/roll.py`: the former picks a named text style, the latter adds a `breakdown` key to `--json` output; `--json` without `--detail` emits the same keys as before
- Dropped-dice display options: `RollFormat(dropped=...)` shows, hides (`HIDDEN`), or marks (`MARKED` with a configurable `dropped_marker`) dice that were dropped, and `show_rerolls=False` renders only a rerolled die's final face while always keeping explosion faces
- `RollFormat` presets (`STANDARD`, `MINIMAL`, `COMPACT`, `VERBOSE`), `RollResultSet.format(fmt=None)` for rendering a roll many ways, and `set_default_format()` / `get_default_format()` for an application-wide default that never affects `str(result)`
- `RollFormat`, a frozen options object holding every display choice (`layout` template, notation, dropped-dice handling, reroll display, modifier depth, separators, glyphs, Fudge symbols, percentile style) with construction-time layout validation
- `DefaultFormatter` and the `Formatter` protocol: a subclassable renderer that folds over a roll breakdown, with `Dropped` and `Percentile` enums, all exported from the package root
- Structured roll breakdown: `RollResult.breakdown` and `RollResultSet.breakdown` as frozen dataclasses (`DiceGroup`, `Die`, `RollBreakdown`, the expression-tree `Literal`/`DiceNode`/`UnaryOp`/`BinaryOp` nodes), exported from the package root, with a JSON-serialisable `RollBreakdown.to_dict()`
- Per-die roll provenance: each `RollResult` now records `dice_traces` (faces, their `roll`/`reroll`/`explosion` source, and the die's value) alongside `all_rolls`
- Index-based `kept_indices` / `dropped_indices` on `RollResult`, so a dropped die is unambiguous when two dice tie
- Characterization snapshot suite pinning default roll rendering for 69 corpus entries (`tests/data/format_snapshots.json`), backed by `tests/format_corpus.py` and the `tools/gen_format_snapshots.py` generator

### Changed

- All rendering now flows through a single `DefaultFormatter` over the structured breakdown; the per-class renderers (`RollResultSet._build_formula_parts`, `RollResult._format_rolls_display`, `_build_cross_dice_string`, `_build_math_operation_string` and `FudgeDiceFormatter`) are gone, and the two Flux `__str__` overrides are replaced by `to_node`
- Retired Spec Kit: removed `.specify/` and `.pi/speckit.*` artifacts; the project constitution now lives at `planning/constitution.md` and feature specs, plans, and task lists moved to `planning/features/`
- Rewrote `AGENTS.md` around the constitution principles, the verification contract, and general working principles

### Fixed

- Precedence-correct parenthesisation in roll descriptions: parentheses the user wrote are no longer dropped, and redundant parentheses are no longer added. Five renderings change, all totals unchanged: `(2d6 + 3) x 2 + 1d4 - 1` becomes `17 = (5 (2d6: 4, 1) + 3) x 2 + 2 (1d4: 2) - 1`; `10 - 2 x 3` becomes `4 = 10 - 2 x 3`; `2d6 + 7 x 4 x 2` becomes `62 = 6 (2d6: 1, 5) + 7 x 4 x 2`; `2d8 - 1d6 - 1 x 4` becomes `5 = 14 (2d8: 6, 8) - 5 (1d6: 5) - 1 x 4`; `2d10 - 7 / 4 - 1d4` becomes `9 = 11 (2d10: 7, 4) - 7 / 4 - 1 (1d4: 1)`

## v0.0.3 (2026-05-04)

### Added

- `rng=` parameter on `Dice.roll()` and the `roll()` convenience function: any object with a `random() -> float` method is accepted (duck-typed), making rolls reproducible from a single seeded instance across all dice, including modifier expressions
- `--seed N` flag on `tools/roll.py` for reproducible command-line rolls; seed value included in `--json` output

## v0.0.2 (2025-10-14)

### Fixed

- Fixed [bug](https://github.com/wyrdbound/wyrdbound-dice/issues/6) where keep/drop operations after reroll or explode operations were ignored (e.g., `4d6r<=2kh3` now correctly keeps the highest 3 dice after rerolling)
- Corrected incorrect GH user in links in pyproject.toml

## v0.0.1 (2025-07-28)

### Added

- Initial release
- Complete dice expression parser with mathematical precedence
- Support for major RPG dice mechanics
- Comprehensive test suite with decent coverage
- CLI tools for rolling and analyzing dice expressions
- Thread-safe operation
- Unicode support
- Debug logging for trouble-shooting and logger configuration
- Extensive documentation and examples
