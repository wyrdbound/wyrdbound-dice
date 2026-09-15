# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Structured roll breakdown: `RollResult.breakdown` and `RollResultSet.breakdown` as frozen dataclasses (`DiceGroup`, `Die`, `RollBreakdown`, the expression-tree `Literal`/`DiceNode`/`UnaryOp`/`BinaryOp` nodes), exported from the package root, with a JSON-serialisable `RollBreakdown.to_dict()`
- Per-die roll provenance: each `RollResult` now records `dice_traces` (faces, their `roll`/`reroll`/`explosion` source, and the die's value) alongside `all_rolls`
- Index-based `kept_indices` / `dropped_indices` on `RollResult`, so a dropped die is unambiguous when two dice tie
- Characterization snapshot suite pinning default roll rendering for 69 corpus entries (`tests/data/format_snapshots.json`), backed by `tests/format_corpus.py` and the `tools/gen_format_snapshots.py` generator

### Changed

- Retired Spec Kit: removed `.specify/` and `.pi/speckit.*` artifacts; the project constitution now lives at `planning/constitution.md` and feature specs, plans, and task lists moved to `planning/features/`
- Rewrote `AGENTS.md` around the constitution principles, the verification contract, and general working principles

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
