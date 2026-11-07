Scope version: 1

# wyrdbound-dice — Scope

## 1. What this is

A dice-rolling library for tabletop RPGs, written in Python with no runtime
dependencies, and two CLI tools over it (`tools/roll.py`, `tools/graph.py`). Its
first consumer is [wyrdbound](https://github.com/wyrdbound), a text-based RPG
engine; anything else that rolls dice for a table (bots, character builders,
virtual tabletops) is a consumer too.

What already ships (0.3.0): standard dice and arithmetic with correct precedence;
keep/drop chains (`kh`, `kl`, `dh`, `dl`); limited and unlimited rerolls;
exploding dice (`e`, `e6`, `e>=5`); Fudge dice; the FUDGE, BOON, BANE, FLUX,
GOODFLUX, BADFLUX and PERC shorthands; named modifiers; seedable, injectable
randomness (`rng=`); bounded work per expression; one grammar checked before any
die is rolled, exposed as `validate()`; a structured breakdown of every roll and
pluggable formatting; and debug tracing. `README.md` documents all of it.

[`constitution.md`](constitution.md) is binding on everything here: zero runtime
dependencies, Python 3.12+, every feature reachable from the CLI, test-first,
mathematically exact, faithful to each game's published rules, observable.

## 2. Requirements

| # | Requirement |
|---|---|
| R1 | A dice pool can count successes instead of summing: each die meeting a target (`10d10>=8`) counts one, and a failure condition (`f1`) subtracts one, as in World of Darkness, Shadowrun and Blades in the Dark. The roll's total is the success count, and its breakdown shows which dice succeeded and which failed. |
| R2 | The library computes the exact probability of every outcome of an expression, without rolling, and `tools/graph.py` draws from it instead of simulating rolls. |
| R3 | The common explosion notations work: `!` as an alias for an explosion on the die's maximum, compounding explosions (`!!`, one die's explosions added into a single value) and penetrating explosions (`!p`, each explosion one less, as in HackMaster); and `ADV` and `DIS` are shorthands for D&D 5e advantage (`2d20kh1`) and disadvantage (`2d20kl1`). |
| R4 | The defects deferred from the roll-formatting plan (`done/roll-formatting.md` §9) are settled: `DiceExpression.evaluate()` reports the total the roll renders rather than the kept dice's subtotal, or the difference is documented as intended; and a reroll or explosion condition that no face can meet (`1d6e<=0`) is reported, not silently accepted. |

## 3. Decisions

| # | Decision | Answer and reason |
|---|---|---|
| D1 | Supported Python | 3.12 and later only (constitution 1.1.0). Older versions stay on 0.3.0. |
| D2 | Runtime dependencies | None, ever, in `src/`. Exact probability (R2) is computed with the standard library; `matplotlib` stays an optional extra for `tools/graph.py` only. |
| D3 | Rendering beyond plain text | Out. No ANSI, Markdown or Rich in the library; consumers style the structured breakdown themselves (`done/roll-formatting.md` §10). |
| D4 | Changes to what an existing valid expression means | Only with a breaking-change entry in `CHANGELOG.md` and a version bump that says so. The format snapshots (`tests/test_format_snapshots.py`) pin rendered output; a feature that changes one says why in its plan. |
| D5 | Where notation comes from | Each game's published rules, and the notation Roll20 and Foundry use where the games don't define one. A plan that picks a notation cites its source. |

## 4. Out of scope

- A markup engine or styled output (D3).
- A dice server, HTTP API, bot or UI. Consumers build those on the library.
- Game logic beyond the roll: initiative order, damage resolution, character
  sheets.

## 5. Roadmap

| # | Feature | Covers | Delivers |
|---|---|---|---|
| V01 | Success counting | R1 | Target and failure conditions on a pool, the success count as the total, successes and failures in the breakdown and formatter, `validate()` and the CLI's `--json` aware of them. |
| V02 | Exact probability distribution | R2 | A public function returning each outcome's exact probability for an expression, its limits on expressions too large to compute, and `tools/graph.py` drawing from it. |
| V03 | More explosion notation | R3 | `!`, `!!` and `!p`, the `ADV` and `DIS` shorthands, and README and CLI coverage of each. |
| V04 | Deferred defects | R4 | A decision on `evaluate()`'s value and its fix or documentation, and a clear error for conditions no face can meet. |
