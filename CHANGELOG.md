# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Arithmetic on a dice count of two or more digits. The lexer decided "dice or number" by peeking one character, so `10d6` lexed as the number `10` and an invalid `d`, and the expression fell back to a method that sums dice and drops everything else: `10d6 - 10d6` totalled 80 instead of 0 and `10d6 + 3` totalled 40 instead of 43
- Text the grammar does not describe is a `ParseError` instead of being ignored. A parser error used to fall back to rolling every dice term it could find: `1d20+{{ x }}`, `2d6 banana`, `2d6+3 # note` and `1d6r` all rolled, silently dropping the rest
- Two different shorthands in one expression both expand. `FUDGE + BOON` expanded to `FUDGE + 3d6kh2`, and any shorthand uppercased the rest of the expression; shorthands now expand as whole words in any case and leave the rest as written
- `GOODFLUX` and `BADFLUX` must be the whole expression; `GOODFLUX + 3` rolled plain flux and dropped the `+ 3`
- Percentile sides (`1d%`), drop modifiers (`4d6dh1`), spaced keep/drop (`4d6 dh 3`) and terms ending in `r` or `k` are parsed directly rather than only through the fallback, which also turned a `TypeError` into the `ParseError` it should always have been

### Changed

- **Breaking:** dice separated only by whitespace are an error. `3d6 5d8` summed both terms; nothing documented it and it is indistinguishable from a missing operator. Write `3d6 + 5d8`
- Every expression is checked against one grammar before any die is rolled, and there is no fallback parser. Output for every expression that was valid is unchanged

## v0.1.0 (2026-09-16)

### Security

These affect anyone upgrading from 0.0.3. Rendered output changes are listed
under Fixed.

- Bounded the work one expression can do, via `MAX_EXPRESSION_LENGTH` (1,000), `MAX_DICE_COUNT` (10,000), `MAX_DIE_SIDES` (1,000,000) and `MAX_TOTAL_DICE` (20,000), each raising `ParseError`. Anything accepting expressions from users was previously a one-line denial of service: `1000000000d6` never returned, a 2,000-digit dice count hung the process, a 20,000-character expression spent over a second in validation before rolling a die, and `9999d6+9999d6+…` packed to 1,000 characters rolled 1.43 million dice for roughly ten seconds of CPU and 650 MB of peak memory. `MAX_TOTAL_DICE` bounds the whole expression, not a single term. The limits are importable from `wyrdbound_dice.dice` and documented in README under "Input Limits"
- `MAX_TOTAL_DICE` is also enforced at runtime, because rerolls and explosions add dice as they go. The infinite-condition validator only rejects conditions matching *every* face, so a nearly-always-true one passed it: `1d1000000e>=2` named a single die and rolled it ~235,000 times, and sixty such terms in one 1,000-byte expression did not finish. A roll that exhausts the budget now raises `InfiniteConditionError`
- `tools/graph.py` HTML-escapes the dice expression and the example rolls before interpolating them into the statistics page it generates. The tool opens that page in a browser, so an expression such as `2d6<script>…</script>` previously executed script in a `file://` origin
- Debug state is per-thread and restored in a `finally`. It was a single module global that `Dice.roll` set on entry and cleared on exit, so a roll that raised left debug enabled for everything after it, and two concurrent debug rolls shared one logger — one thread's output silently went to a logger the other owned
- Debug records escape newlines and carriage returns in caller-supplied text, which could otherwise forge a whole log record, for example `1d6\nDEBUG: [COMPLETE] Final result: 999999`
- Both GitHub workflows declare `permissions: contents: read` rather than inheriting the default token scope, and the release workflow publishes through PyPI Trusted Publishing (OIDC, scoped to the `pypi` environment) instead of a long-lived API token

### Added

- `--format {standard,compact,minimal,verbose}` and `--detail` flags on `tools/roll.py`: the former picks a named text style, the latter adds a `breakdown` key to `--json` output; `--json` without `--detail` emits the same keys as before
- Dropped-dice display options: `RollFormat(dropped=...)` shows, hides (`HIDDEN`), or marks (`MARKED` with a configurable `dropped_marker`) dice that were dropped, and `show_rerolls=False` renders only a rerolled die's final face while always keeping explosion faces
- `RollFormat` presets (`STANDARD`, `MINIMAL`, `COMPACT`, `VERBOSE`), `RollResultSet.format(fmt=None)` for rendering a roll many ways, and `set_default_format()` / `get_default_format()` for an application-wide default that never affects `str(result)`
- `RollFormat`, a frozen options object holding every display choice (`layout` template, notation, dropped-dice handling, reroll display, modifier depth, separators, glyphs, Fudge symbols, percentile style). `layout`, `dropped_marker` and `fudge_symbols` are validated at construction and the two templates are substituted by a scanner accepting only bare placeholders plus the `{{` and `}}` escapes, so a format cannot reach through a component with attribute access or allocate unbounded memory with a format spec, and cannot fault mid-render
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
