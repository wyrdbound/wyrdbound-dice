# Roll Formatting — separating what happened from how it reads

**Status:** Designed. Not started.
**Companion docs:** `AGENTS.md` (the constitution summary — Articles I–VI are
binding here), `README.md` (the API this changes), `CHANGELOG.md`.
**Touches:** `src/wyrdbound_dice/breakdown.py` (new), `formatting.py` (new),
`roll_result.py`, `expression_parser.py`, `dice.py`, `__init__.py`;
`tools/roll.py`, `tools/gen_format_snapshots.py` (new); `tests/format_corpus.py`,
`tests/data/format_snapshots.json`, `tests/test_format_snapshots.py`,
`tests/test_breakdown.py`, `tests/test_formatting.py`, `tests/test_cli_format.py`.
**Does not touch:** the RNG path, any dice value or distribution, `Dice.roll()`'s
signature, `expression_lexer.py`, `expression_token.py`, `debug_logger.py`,
`errors.py`, `tools/graph.py`, or any existing test file.

---

## 1. Problem

You cannot ask this library to show a roll any other way, and the reason is
structural rather than missing-feature.

`Dice.roll("2d6 + 3")` returns a `RollResultSet` whose rendered form was decided
during evaluation and frozen into a string. `expression_parser.py` defines
`EvaluationResult(value, description, dice_results)`, where `description` is
assembled bottom-up by `DescriptionBuilder` as each node evaluates. By the time
`Dice.roll()` returns, the parse tree is gone; `_parse_with_precedence` stores
the finished string on `RollResultSet._override_description`, and
`RollResultSet.__str__` returns it verbatim. Four more renderers —
`RollResult.__str__`, `RollResultSet._build_formula_parts`,
`RollModifier.__str__` and `FudgeDiceFormatter` — each build fragments inline.

`ExpressionProcessor.should_use_precedence_parsing()` sends anything containing
`x`, `*`, `×`, `/`, or a `+`/`-` next to a digit down that path, which is very
nearly every expression anyone writes. So for almost every roll, the only record
of how it was assembled is a string.

That is the headline. Building the feature surfaced four further defects, two of
which are real bugs.

### (a) Parenthesisation is decided by looking at rendered text, and it is incoherent

`DescriptionBuilder.build_binary_description()` decides whether to parenthesise
by calling `.isdigit()` on the left and right *descriptions*, and rewrites
`+ -B` into `- B` with `_remove_leading_minus()`, again by string inspection.
Verified against v0.0.3 with `rng=random.Random(42)`:

| Expression | v0.0.3 rendering | What is wrong |
| --- | --- | --- |
| `(2d6 + 3) x 2 + 1d4 - 1` | `17 = 5 (2d6: 4, 1) + 3 x 2 + 2 (1d4: 2) - 1` | The parentheses the user wrote are **dropped**. Read literally the rendering says `5 + (3 × 2) + 2 − 1 = 12`; the total printed beside it is 17. The description does not describe the arithmetic. |
| `10 - 2 x 3` | `4 = 10 - (2 x 3)` | Parentheses **added** where precedence already implies them. |

Both wrong, in opposite directions, decided by whether the operands happened to
render as bare digits. This is the one place where the feature must change
default output — see §4.1.

### (b) `all_rolls` loses provenance and die identity

In `_roll_single_dice_expression`, `all_rolls` is a flat list appended to in
three places: the initial roll of each die, each reroll, and each explosion.
`rolls` holds one entry per die with explosion values already summed in. Nothing
records which `all_rolls` entry belongs to which die, or whether an entry was an
initial roll, a reroll or an explosion. "Which die was dropped" and "this face
was a reroll" cannot be reconstructed after the fact; they have to be recorded
while rolling.

One ordering fact is worth relying on: `all_rolls` is appended in die order, and
within a die in roll order. Concatenating each die's faces in order reproduces it
exactly, which is what makes byte-identical default output achievable at all.

### (c) Kept and dropped are computed and never shown

`RollResult._calculate_kept_and_dropped()` populates `self.kept` and
`self.dropped`. `_format_rolls_display()` renders `all_rolls`. So `4d6kh3`
prints `4, 1, 2, 2` and never says which die was dropped. The data is right
there, unused.

Worse, `KeepOperationProcessor` sorts *values* and returns value lists, so when
two dice tie there is no way to say which one was dropped. Index-carrying is
required for correctness, not tidiness.

### (d) Dead code that must not be carried forward

`RollResultSet._build_formula_parts()` guards on
`hasattr(self, "_has_leading_zero_minus") and self._has_leading_zero_minus`. The
attribute is never assigned anywhere in `src/`, `tests/` or `tools/` — the
branch is unreachable. (The leading `0 - ` in `-1d6` comes from
`ExpressionProcessor.process_negative_dice` rewriting the expression, not from
any rendering special case.)

### What this costs downstream

`tools/roll.py --json` ships `{"result": 14, "description": "14 = 14 (1d20: 14)"}`
— a pre-rendered string where a consumer wants data. Article II asks for JSON
output; what it gets is a screenshot.

---

## 2. What already exists

| Thing | State |
| --- | --- |
| `ExpressionParser` builds a real AST (`parse_expression`/`parse_term`/`parse_factor`) | **Shipped.** Only `evaluate()` discards it. This feature recovers structure that already exists. |
| `RollResult.keep_operations` / `drop_operations` as structured tuples | **Shipped.** Already the right shape. |
| `RollResult.kept` / `dropped` | **Shipped**, computed on every roll, never displayed. |
| `RollResult.all_rolls` | **Shipped**, flat, no provenance (§1b). |
| Fudge raw→symbol mapping (`≤2 → -`, `≤4 → B`, else `+`) | **Shipped** in `FudgeDiceFormatter`. Correct; needs parameterising, not rewriting. |
| Percentile `[tens, ones]` rendering with the `:02d` guard | **Shipped** in `_format_rolls_display`. |
| Notation assembly (`_build_keep_string`, `_build_drop_string`, `_build_reroll_string`, `_build_explode_string`) | **Shipped** and correct. Reused verbatim. |
| `rng=` injection, duck-typed | **Shipped** (feature 001). The precedent this feature follows for `Formatter`. |
| `--json`, `--debug`, `--seed` on `tools/roll.py` | **Shipped.** Keys must not change. |
| A structured breakdown of a roll | **Missing.** The whole feature. |
| Any way to re-render a roll | **Missing** (§1). |
| Tests asserting exact rendered strings | **Almost missing.** Only `tests/test_base.py` and `tests/test_convenience_function.py`, two assertions between them. §7 exists because of this. |

No schema, no dependencies, no new runtime behaviour during rolling. This is a
data-model recovery plus a renderer.

---

## 3. The model

### 3.1 The breakdown is the roll; the format is a view of it

Two new modules, deliberately separable so a consumer can depend on the data
without the policy:

- `breakdown.py` — what happened. `Die`, `DiceGroup`, an expression-tree node
  union, `ModifierBreakdown`, `RollBreakdown`, `to_dict()`.
- `formatting.py` — how it reads. `RollFormat`, `Dropped`, `Percentile`, the
  `Formatter` protocol, `DefaultFormatter`, the module default.

Everything renderable is a fold over a `RollBreakdown`. `__str__` becomes one
call into `DefaultFormatter` with the default format, and nothing else in the
package builds a string.

### 3.2 A die remembers its own faces

```python
@dataclass(frozen=True)
class Die:
    value: int                       # this die's contribution to the subtotal
    faces: Tuple[Any, ...] = ()      # every face rolled for it, in roll order
    sources: Tuple[str, ...] = ()    # parallel: "roll" | "reroll" | "explosion"
    kept: bool = True
```

`faces` entries are `int` for standard and Fudge dice — Fudge stores the **raw**
1–6 value, matching `all_rolls` — and `(tens, ones)` tuples for percentile dice.
`len(sources) == len(faces)` always.

**Invariant, and the reason byte-identical output is possible:** concatenating
`faces` across a group's dice in order reproduces that group's `all_rolls`
exactly. Assert it in tests; it is load-bearing.

### 3.3 Kept and dropped are positions, not values

`KeepOperationProcessor` gains an index-carrying twin for each method, returning
`(kept_indices, dropped_indices)`. `RollResult` gains `kept_indices` and
`dropped_indices` as the authoritative mapping; `kept` and `dropped` stay as
value lists so no existing caller breaks. With `[3, 3, 5, 1]` and `kh2`, exactly
one of the two 3s is kept, and the breakdown must be able to say which.

### 3.4 The expression tree, recovered

```python
@dataclass(frozen=True)
class Literal:   value: int
@dataclass(frozen=True)
class DiceNode:  group: DiceGroup
@dataclass(frozen=True)
class UnaryOp:   op: str; operand: Node; value: int
@dataclass(frozen=True)
class BinaryOp:  left: Node; op: str; right: Node; value: int

Node = Union[Literal, DiceNode, UnaryOp, BinaryOp]
PRECEDENCE = {"+": 1, "-": 1, "x": 2, "/": 2}
```

`op` holds the **canonical** symbol that `OperatorHandler.evaluate_binary_operation`
already returns (`"+"`, `"-"`, `"x"`, `"/"`). The user's chosen glyph is
substituted at render time and never stored in the tree.

`EvaluationResult.description` becomes a property rendering `node`, so
`_override_description` keeps working while the refactor lands in steps.

### 3.5 `layout` arranges components; options render them

`"12 = "` is not one thing. It is a component (the total) plus an arrangement
decision (where it sits, what joins it). Bundling them into a content enum
fixes three arrangements and forbids every other. So the total is exposed as a
component and a single flat template arranges it:

```python
layout: str = "{total} = {breakdown}"
```

| `layout` | Output |
| --- | --- |
| `"{total} = {breakdown}"` (default) | `17 = 8 (2d6: 6, 2) + 3` |
| `"{breakdown}"` | `8 (2d6: 6, 2) + 3` |
| `"{total}"` | `17` |
| `"{breakdown} => {total}"` | `8 (2d6: 6, 2) + 3 => 17` |
| `"{expression}: {total}"` | `2d6 + 3: 17` |

This is the one place a template belongs, and the distinction is the whole
design: **templates arrange components; options render them.** At the top level
there is exactly one total, one breakdown and one expression — no repetition, no
nesting, three placeholders, no grammar to invent. Repeating structure (dice,
modifiers, nested modifier rolls) is never templated; it is rendered by
`DefaultFormatter` under the typed options in §5. §10 says what happens if that
line is crossed.

Three consequences that must be built, not assumed:

- Validation happens in `__post_init__`, at construction time, so a bad layout
  fails where it was written rather than at some later render.
- The layout string is the only text `str.format` parses. A brace produced by a
  custom `dropped_marker` is substituted in as literal text and never re-scanned.
- When `{breakdown}` is absent, the breakdown is not rendered at all.

### 3.6 Flux is a subtraction, not a special case

`GoodFluxResult.__str__` and `BadFluxResult.__str__` hand-render
`"{high} (1d6: {high}) - {low} (1d6: {low})"`. That is precisely what
`BinaryOp(DiceNode(1d6), "-", DiceNode(1d6))` renders through the generic
formatter. Both overrides are deleted rather than ported, and flux stops being
a special case in the codebase.

---

## 4. What this feature must fix to ship

### 4.1 Parenthesisation must come from precedence — and this changes output

Replace the `.isdigit()` heuristic with the tree: parenthesise a `BinaryOp` child
when its operator binds more loosely than the parent's, or equally loosely on the
**right** of `-` or `/`.

This is the single deliberate exception to byte-identical output. It is a
correctness fix — the current rendering of `(2d6 + 3) x 2 + 1d4 - 1` contradicts
its own total — but it is still a visible change, so it is gated: the snapshot
diff must be enumerated, signed off, and recorded in `CHANGELOG.md` as a fix. An
executing agent may not wave it through. **No other output change is permitted.**

### 4.2 The roll loop must record provenance

Build a per-die trace alongside `all_rolls` at the three points where `all_rolls`
is appended (§1b). `all_rolls` itself is not touched.

### 4.3 Keep/drop must carry indices

§3.3. Without it, ties are unresolvable and `Dropped.MARKED` marks the wrong die.

### 4.4 `__str__` must go through the formatter

`RollResultSet.__str__`, `RollResult.__str__`, `_build_formula_parts`,
`_format_rolls_display`, `FudgeDiceFormatter` and the two flux overrides all
collapse into one path. Six renderers become one.

---

## 5. The format object

```python
@dataclass(frozen=True)
class RollFormat:
    layout: str = "{total} = {breakdown}"

    show_notation: bool = True
    dropped: Dropped = Dropped.SHOWN
    show_rerolls: bool = True
    modifier_depth: int = 2

    die_separator: str = ", "
    group_open: str = "("
    group_close: str = ")"
    notation_separator: str = ": "
    multiply_symbol: str = "x"
    divide_symbol: str = "/"
    dropped_marker: str = "~{value}~"
    fudge_symbols: Tuple[str, str, str] = ("-", "B", "+")
    percentile: Percentile = Percentile.PAIR
```

Every default reproduces v0.0.3. `RollFormat()` and `RollFormat.STANDARD` compare
equal. Frozen, so `dataclasses.replace()` is the derivation path and a format is
safe to share as a module default.

| Field | Effect |
| --- | --- |
| `layout` | §3.5. |
| `show_notation` | `False` renders `(6, 2)` instead of `(2d6: 6, 2)`. |
| `dropped` | `SHOWN` (v0.0.3) · `HIDDEN` · `MARKED`, which wraps with `dropped_marker`. |
| `show_rerolls` | `False` renders only each die's final face, omitting superseded rerolls. Explosion faces still render — they all contribute to the value. |
| `modifier_depth` | `0` → `+ 3` · `1` → `+ 3 (Bless)` · `2` → `+ 3 (Bless: 3 = 3 (1d4: 3))`. Above 2 behaves as 2. |
| `fudge_symbols` | `(minus, blank, plus)` for raw 1–2, 3–4, 5–6. |
| `percentile` | `PAIR` → `[00, 5]` · `VALUE` → `05`. |

Presets are ordinary instances — nothing about them is privileged:

```python
RollFormat.STANDARD = RollFormat()
RollFormat.MINIMAL  = RollFormat(layout="{total}")
RollFormat.COMPACT  = RollFormat(die_separator=",", notation_separator=":",
                                 modifier_depth=1, dropped=Dropped.HIDDEN,
                                 show_rerolls=False)
RollFormat.VERBOSE  = RollFormat(dropped=Dropped.MARKED)
```

---

## 6. The public surface

```python
result.format(fmt=None) -> str        # None → module default → STANDARD
result.breakdown        -> RollBreakdown
result.breakdown.to_dict() -> dict    # json.dumps-able, no custom encoder

set_default_format(fmt) / get_default_format()

class Formatter(Protocol):
    def format(self, breakdown: RollBreakdown) -> str: ...

class DefaultFormatter:               # override points, stable within a major
    def format(self, breakdown) -> str
    def format_node(self, node, parent_precedence=0) -> str
    def format_group(self, group) -> str
    def format_die(self, die, group) -> str
    def format_modifier(self, modifier) -> str
```

`result.format(RollFormat.STANDARD) == str(result)` for every roll. Formatting a
successfully-evaluated result never raises and never rolls a die.

The module default is display state read only at render time. It never affects
`__str__` and is never read during evaluation, so Article IV's prohibition on
global mutable state *during rolling* is untouched. Documented as set-once at
startup; not synchronised, not per-thread.

`Dice.roll()` does **not** gain a formatting parameter. It already carries five,
and a result should be renderable many ways after the fact.

CLI: `--format {standard,compact,minimal,verbose}` for text output, and
`--detail` which adds a `breakdown` key under `--json`. `--json` without
`--detail` emits exactly the v0.0.3 keys.

---

## 7. The characterization corpus

Two assertions in the whole existing suite touch rendered strings (§2). The
refactor rewrites the evaluator. Those two facts together mean the corpus is a
prerequisite, not a nicety.

`tests/format_corpus.py` holds 63 expressions and 7 modifier cases, all verified
against v0.0.3 at seed 42. `tools/gen_format_snapshots.py` renders each and
writes `tests/data/format_snapshots.json`; `tests/test_format_snapshots.py`
re-rolls and asserts byte equality. Entries are **append-only** — never edited,
never reordered — because their snapshots are the regression contract.

Error paths are entries too: a snapshot value of `"!DivisionByZeroError"` pins
the exception as firmly as a rendering pins a string.

Empirical notes from building it, all confirmed at seed 42:

- `-1d6` renders `-4 = 0 - 4 (1d6: 4)` — the `0 - ` comes from
  `process_negative_dice`, not from rendering (§1d).
- `4d6r<=2kh3` renders its notation as `4d6kh3r<=2`: keep, drop, reroll, explode.
- `1d6e` and `2d6e` render the materialised target (`1d6e6`).
- `1d6e<=0` does **not** raise; it rolls normally (§9.3).
- `1d20` with `{"Bane": "-1d4"}` renders `- 1 (Bane: 1 = 1 (1d4: 1))` — the
  nested roll shows its **unsigned** value with the sign outside.

---

## 8. Constitution check

| Article | Status |
| --- | --- |
| I — Library-first, zero deps | Two self-contained modules; `dataclasses`, `enum`, `typing` only. |
| II — CLI protocol | `--format` and `--detail` added; existing flags and JSON keys preserved. |
| III — Test-first | Characterization suite first, then failing unit tests per phase, then implementation. |
| IV — Mathematical precision | No value or distribution changes. Parenthesisation moves from a string heuristic to true precedence — strictly more correct. |
| V — RPG system fidelity | Fudge symbols, percentile pairs, flux and keep/drop notation unchanged by default; Fudge symbols become configurable without changing the default. |
| VI — Observability | `--json --detail` exposes the breakdown; debug logging untouched. |

Python 3.8 is the floor: `typing.Tuple`/`Optional`/`Union`, no builtin generics,
no `X | Y`, no `slots=True`.

---

## 9. Defects found and deliberately left out

### 9.1 `DiceExpression.evaluate()` reports `subtotal`, not the adjusted total

`evaluate()` returns `value=result.subtotal` (sum of kept dice) while
`RollResult.__str__` renders `(kept_sum * multiply) // divide`. The regex-level
`xN` / `/N` suffixes therefore affect the rendered group but not the value folded
into the enclosing expression. Whether that is intentional is **unresolved**. The
tree refactor puts the two adjacent and will force the question. Do not change it
to "fix" it — the snapshots define current behaviour, and a silent change here
alters totals, which is the one thing this feature must not do.

### 9.2 `_has_leading_zero_minus` is unreachable

§1d. Deleted, not ported. Confirm with `grep -rn "_has_leading_zero_minus"
src/ tests/ tools/` before deleting.

### 9.3 `1d6e<=0` does not raise

`DiceExpressionValidator.validate_explosion_condition` is expected to catch an
always-true explosion condition, and does not fire here. Recorded as a corpus
entry pinning current behaviour. Fixing it changes which expressions raise —
a separate change with its own decision.

---

## 10. What this is not

**Not a markup engine.** No ANSI, no Markdown, no Rich. Each would add a styling
vocabulary to `RollFormat` and a correctness burden (escaping, width, nesting)
with no clear stopping point, and would put presentation policy in a library
whose primary consumer — wyrdbound, a text-based RPG engine — has its own. The
breakdown gives consumers everything they need to do it themselves and better.
`DefaultFormatter` is subclassable precisely so this stays out.

**Not a template language for repeating structure.** `"{total} = {expr}: {rolls}"`
reads well in a README and fails on contact: the interesting structure is nested
and repeating — per group, per die, per modifier, recursively for modifier dice.
A flat `str.format` cannot say "render each die, marking the dropped ones". The
fix is loops, which means either a template engine (a dependency, forbidden by
Article I) or a grammar this project then owns — escaping rules, error messages
for malformed templates, a compatibility surface. §3.5's `layout` is a template
at the one level where there is nothing to loop over. That boundary is the design.

**Not a formatting parameter on `Dice.roll()`.** §6.

**Not `__format__` sugar.** `f"{result:compact}"` is charming, limits the format
to a single identifier, and hides a lookup table behind a string. It can be added
later over presets without disturbing anything here.

**Not a fix for §9.1 or §9.3.** Both change values or raising behaviour.

---

## 11. Decisions

1. **A structured breakdown is the foundation, not the formatter.** Everything
   renderable is a fold over it, and it independently fixes `--json`.
2. **`layout` replaces a content enum and a separator field.** One field, more
   expressive, no invalid states (§3.5).
3. **`RollFormat`, not `DiceFormat` or `RollResultFormat`.** It formats a roll.
   `RollResultFormat` would point at `RollResult`, the inner per-group type,
   while the thing being formatted is a `RollResultSet`.
4. **Frozen dataclass over a builder.** Hashable, shareable as a module default,
   `dataclasses.replace()` for free, no `__init__` boilerplate.
5. **`Formatter` as a `typing.Protocol`.** Structural typing, matching the
   duck-typed `rng=` precedent from feature 001.
6. **Plain text only.** §10.
7. **Precedence-correct parenthesisation is in scope, gated.** §4.1. The
   alternative is carrying the `.isdigit()` heuristic forward forever.
8. **Dropped-dice display is opt-in, so this is a MINOR bump.** `STANDARD`
   output is unchanged; new display is reachable only through non-default
   formats.

---

_Version: 0.1 | Last updated: 2026-09-15_
