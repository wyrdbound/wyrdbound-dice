# Roll Formatting — the breakdown, the formatter, and the byte-identical gate

**Status:** Phase 5 complete (T053–T064 done; 284 passing, 1 xfail pending T075;
checkpoint 5 patch bump to 0.0.8). Phase 6 next.
**Source design:** `planning/features/roll-formatting.md` (v0.1; §N references
below are into that document). `AGENTS.md` — the constitution summary and the
Verification Contract — is binding on every task here.
**Scope:** a structured breakdown of a roll; a `RollFormat` options object with
a `layout` template and four presets; a subclassable `DefaultFormatter`; an
optional module default; the evaluator refactor that makes all of it possible;
`--format` and `--detail` on the CLI.
**Deferred:** ANSI/Markdown rendering, per-die and per-group templates,
`__format__` sugar, the `subtotal`-vs-multiply/divide question (§9.1), the
`1d6e<=0` validator gap (§9.3). See §Deferred at the end.

---

## How to execute this list

This list is written to be run **one task at a time by a model that does not
hold the design doc in context**. Every task names its files, restates the rule
it implements, and states its own acceptance check. Do not read ahead; do not
batch.

`planning/features/README.md` — the global rules for the executing agent — is
binding on every task here.

### Progress tracking — mandatory

**Check the box** (`- [x]`) on every task the moment it is done, and keep the
`**Status:**` header current. This file is the shared ledger for the slice: an
agent picking it up mid-way reads the status header and the checked boxes to
know where work stopped. A task is "done" only when its commit is in the repo;
check the box in the same commit, never before. One task → one checkbox → one
commit.

### Per-task definition of done

1. The named file(s) exist with the described content, and nothing else changed.
2. `black src/ tests/ tools/` and `isort src/ tests/ tools/` produce no diff;
   `ruff check src/ tests/ tools/` passes.
3. `python -m pytest tests/ -q` passes (a TDD test task is done when its test
   **fails for the stated reason** — a missing name or a wrong value, never a
   syntax error).
4. The task's stated acceptance check passes.
5. From Phase 1 onward, `python -m pytest tests/test_format_snapshots.py -q` is
   green. This is the regression contract and it is checked after **every**
   task, not only at checkpoints.

### Per-phase definition of done

At each **Checkpoint**, additionally:

- `python -m pytest tests/ -q --cov=wyrdbound_dice` passes.
- No file under `tests/` has been modified except the new test files this list
  creates.
- Version bumped in `pyproject.toml` **and**
  `src/wyrdbound_dice/__init__.py:__version__` — patch bump per checkpoint,
  minor bump at T086 (§11.8: `STANDARD` output is unchanged, so this is MINOR,
  never MAJOR).

### Format

`[ID] [P?] [Story] Description`

- **[P]** — parallelizable: different files, no dependency on an unfinished task.
- **[Story]** — US1…US7 below.

### User stories

| | |
| --- | --- |
| **US1** | Default output does not change. |
| **US2** | A roll's parts are available as data, not as a string to parse. |
| **US3** | A few named styles cover the common cases. |
| **US4** | Every display choice can be overridden individually. |
| **US5** | One style can be set once for a whole application. |
| **US6** | A custom formatter is never blocked by a missing option. |
| **US7** | The CLI exposes all of it. |

### Path conventions

| Thing | Path |
| --- | --- |
| Breakdown types (new) | `src/wyrdbound_dice/breakdown.py` |
| Formatter (new) | `src/wyrdbound_dice/formatting.py` |
| Roll result + keep/drop | `src/wyrdbound_dice/roll_result.py` |
| Evaluator | `src/wyrdbound_dice/expression_parser.py` |
| Orchestration, result set, flux | `src/wyrdbound_dice/dice.py` |
| Public exports | `src/wyrdbound_dice/__init__.py` |
| CLI | `tools/roll.py` |
| Snapshot generator (new) | `tools/gen_format_snapshots.py` |
| Corpus (new) | `tests/format_corpus.py` |
| Snapshots (new, committed) | `tests/data/format_snapshots.json` |
| New tests | `tests/test_format_snapshots.py`, `test_breakdown.py`, `test_formatting.py`, `test_cli_format.py` |

---

## The nine rules that must never be broken

Restate these to yourself before any task. Every one is a failure a
plausible-looking implementation makes.

1. **The snapshot file is the contract, not a convenience.**
   `tests/data/format_snapshots.json` is regenerated exactly once in this list,
   at T056, and only after sign-off. Regenerating it to make a red test go green
   deletes the only thing protecting default output. If it fails, the code is
   wrong until proven otherwise.
2. **No total ever changes.** This feature touches rendering. If a `.total`
   moves, stop — you have changed arithmetic, which is out of scope and is what
   §9.1 warns about.
3. **`all_rolls` is never modified.** Provenance is recorded *alongside* it.
   Every existing consumer reads it and every snapshot depends on it.
4. **Kept and dropped are positions, never values** (§3.3). `[3, 3, 5, 1]` with
   `kh2` keeps one specific 3. A value-based implementation marks the wrong die
   and no round-trip test will notice.
5. **Never edit or delete an existing test.** `AGENTS.md` Verification Contract
   §4. If an existing test fails, that is a defect in the change.
6. **Python 3.8 is the floor.** `typing.Tuple`/`Optional`/`Union`. No `list[int]`,
   no `X | Y`, no `dataclasses(slots=True)`, no `functools.cache`.
7. **`__str__` never reads the module default** (§6). It always renders
   `STANDARD`. An application setting a default must not silently change what
   every `print(result)` in every other library prints.
8. **The layout template is applied to already-rendered text and never
   re-scans it** (§3.5). Only the layout string is parsed by `str.format`. A
   brace produced by a `dropped_marker` is literal output.
9. **Do not fix §9.1 or §9.3.** The `subtotal`-vs-multiply/divide discrepancy and
   the `1d6e<=0` validator gap are recorded, pinned by snapshots, and out of
   scope. Both change values or raising behaviour. File them; do not touch them.

### And three traps with named victims

- **The green-snapshot trap.** At T055 the snapshot suite *will* go red. The
  diff is expected to be the parenthesis cases from §1a and nothing else.
  Regenerating the file makes the suite green and the feature unverifiable in
  the same keystroke. That is the single most damaging thing an agent can do in
  this list, and it looks exactly like progress.
- **The silent-tie trap.** Implement keep/drop on sorted values and everything
  passes: subtotals are right, `kept` and `dropped` hold the right values, the
  round-trip is clean. Only `Dropped.MARKED` reveals it, by striking through a
  die that was kept, in the one case (ties) nobody writes a test for by reflex.
  Rule 4 exists because this is invisible until it ships.
- **The reconstruct-provenance trap.** `all_rolls` looks like it ought to be
  decomposable — count the dice, walk the list. It is not: a die that rerolled
  twice and a die that exploded once are indistinguishable from the outside
  (§1b). Any code that tries to derive `sources` after the roll is wrong, and
  will be *right* on `3d6` and wrong on `8d6r1<=1`. Record it in the loop.

---

## Phase 1 — The characterization net

**Purpose:** freeze current output before touching anything. Nothing here
changes library behaviour. Two assertions in the whole existing suite touch
rendered strings (§2) — this phase is why the rest of the list is safe.

- [x] **T001** [US1] Run `python -m pytest tests/ -q` from the repo root and
  confirm every test passes. Record the passing count; T007 and T085 reference
  it.
  *Accept:* the suite is green and the count is written into the commit message.

- [x] **T002** [P] [US1] Create `tests/format_corpus.py` with exactly three
  module-level names and no test functions: `SEED = 42`, `EXPRESSIONS`, and
  `MODIFIER_CASES`, using the values below **verbatim and in this order**. These
  were verified against v0.0.3 on 2026-09-15; **do not recompute or reorder
  them.** Module docstring: this is the characterization corpus for roll
  rendering, and entries are append-only — never edited, never reordered,
  because their snapshots are the regression contract.

  ```python
  EXPRESSIONS = [
      # basic polyhedral
      "1d20", "3d6", "1d4", "1d8", "1d12", "1d100", "0d6", "-1d6",
      # percentile
      "1d%", "PERC", "PERCENTILE",
      # arithmetic and precedence
      "2d6 + 3", "1d20 - 2", "1d6 x 4", "1d10 / 2", "2d6 + 1d4 x 2 - 1",
      "(2d6 + 3) x 2 + 1d4 - 1", "1d6 - 1d6", "2d6 × 2", "1d10 ÷ 2",
      "5 + 3", "10 - 2 x 3",
      # keep / drop
      "4d6kh3", "2d20kh1", "2d20kl1", "4d6kl3", "4d6dh1", "4d6dl1",
      "5d6kh3kl1", "4d6kh0", "4d6dl0",
      # rerolls
      "1d6r<=2", "1d6r1<=2", "1d6r3<=3", "1d6ro<=2", "4d6r<=2kh3",
      "1d20r=1", "1d6r<2", "1d8r>=7",
      # exploding
      "1d6e", "1d6e6", "1d10e>=8", "1d6e>=5", "2d6e",
      # fudge
      "1dF", "4dF", "4dF + 2", "FUDGE",
      # system shorthands
      "BOON", "BANE", "FLUX", "GOODFLUX", "BADFLUX",
      # combinations
      "8d6r1<=1", "1d8 + 3d6", "2d20kh1 + 8", "1d6e + 2", "4dF + 3",
      "2d6r1<=2",
      # error paths — the snapshot stores "!ExceptionName"
      "1d6 / 0", "1d6r<=6", "1d6e<=0",
  ]

  MODIFIER_CASES = [
      ("1d20", {"Strength": 3}),
      ("1d20", {"Strength": 3, "Proficiency": 2}),
      ("1d20", {"Bless": "1d4"}),
      ("1d20", {"Bane": "-1d4"}),
      ("1d20", {"Strength": 3, "Proficiency": 2, "Bless": "1d4"}),
      ("2d6", {"DM": 1}),
      ("4dF + 3", {"Aspect": 2}),
  ]
  ```
  *Accept:* `python -c "import sys; sys.path.insert(0,'tests'); import format_corpus as c; print(len(c.EXPRESSIONS), len(c.MODIFIER_CASES))"` prints `62 7`.

- [x] **T003** [US1] Create `tools/gen_format_snapshots.py`. Insert `src` on
  `sys.path` the way `tools/roll.py` does, and `tests` as well. For each
  expression roll `Dice.roll(expr, rng=random.Random(SEED))`; for each modifier
  case `Dice.roll(expr, modifiers=mods, rng=random.Random(SEED))`. Record
  `str(result)` on success and `"!" + type(exc).__name__` on any exception. Keys
  are `expr` for plain entries and `expr + " ||| " + json.dumps(mods, sort_keys=True)`
  for modifier entries. Write to `tests/data/format_snapshots.json` with
  `json.dumps(..., indent=2, ensure_ascii=False, sort_keys=True)` plus a trailing
  newline, creating `tests/data/` if needed.
  *Accept:* the script runs without error.

- [x] **T004** [US1] Run `python tools/gen_format_snapshots.py` and commit
  `tests/data/format_snapshots.json`. Spot-check three entries: `"1d20"` is a
  string of the form `"N = N (1d20: N)"`; `"1d6 / 0"` is
  `"!DivisionByZeroError"`; `"1d6r<=6"` is `"!InfiniteConditionError"`.
  *Accept:* the file has exactly 69 entries and the three spot-checks match.

- [x] **T005** [P] [US1] Create `tests/test_format_snapshots.py`: load the JSON
  once at module level, parametrise over `EXPRESSIONS` and `MODIFIER_CASES`,
  re-roll each with `random.Random(SEED)`, and assert the rendered string — or
  `"!" + exception class name` — equals the stored value. Failure messages print
  the key, the expected value and the actual value on separate lines. Module
  docstring, in these words: **this file is the regression contract; do not
  regenerate the snapshot JSON to make it pass.**
  *Accept:* T006.

- [x] **T006** [US1] Run `python -m pytest tests/test_format_snapshots.py -q`.
  All 69 assertions must **pass** — this is a characterization test, not a red
  test. If any entry fails, the generator and the test disagree about key
  construction; fix the test, never the snapshot.
  *Accept:* 69 passed.

- [x] **T007** [US1] Run `black src/ tests/ tools/`, `isort src/ tests/ tools/`,
  `ruff check src/ tests/ tools/`, then `python -m pytest tests/ -q`.
  *Accept:* the passing count is T001's count plus 69.

**Checkpoint 1.** Per-phase gate. Patch bump.

---

## Phase 2 — Per-die provenance

**Purpose:** record which face belonged to which die, where each face came from,
and which die was dropped. Additive only; nothing rendered changes. Read the
reconstruct-provenance trap before starting.

- [x] **T008** [P] [US2] Create `tests/test_breakdown.py` with a module
  docstring, imports (`random`, `pytest`, `from wyrdbound_dice import Dice`),
  and a helper `roll(expr, seed=42, **kw)` returning
  `Dice.roll(expr, rng=random.Random(seed), **kw)`.
  *Accept:* the file imports cleanly.

- [x] **T009** [P] [US2] Write failing `test_dice_traces_present` (TDD): roll
  `"3d6"`, take `result.results[0]`, assert `dice_traces` is a list of length 3
  and each entry is a dict with keys exactly `{"faces", "sources", "value"}`.
  *Accept:* fails with `AttributeError`.

- [x] **T010** [P] [US2] Write failing `test_traces_concatenate_to_all_rolls`:
  for `"3d6"`, `"2d6r1<=2"`, `"2d6e"`, `"4dF"`, `"1d%"`, assert
  `[f for t in r.dice_traces for f in t["faces"]] == r.all_rolls` — same order,
  same values, same types. This is the §3.2 invariant and it is load-bearing.
  *Accept:* fails with `AttributeError`.

- [x] **T011** [P] [US2] Write failing `test_trace_sources_tag_rerolls`: roll
  `"8d6r1<=1"` at seed 42 (the corpus shows this rerolls), assert at least one
  `"reroll"` appears across all traces, that every source is one of `"roll"`,
  `"reroll"`, `"explosion"`, and that the **first** entry of every trace's
  `sources` is `"roll"`.
  *Accept:* fails with `AttributeError`.

- [x] **T012** [P] [US2] Write failing `test_kept_indices_handles_ties`:
  construct `RollResult(4, "6", [3, 3, 5, 1], keep_operations=[("h", 2)])`
  directly from `wyrdbound_dice.roll_result`; assert `len(r.kept_indices) == 2`,
  `len(r.dropped_indices) == 2`, `2 in r.kept_indices`,
  `set(r.kept_indices) | set(r.dropped_indices) == {0, 1, 2, 3}`, and that
  exactly one of index 0 or 1 is in `kept_indices`. This is the silent-tie trap.
  *Accept:* fails with `AttributeError`.

> **Gate.** Run `python -m pytest tests/test_breakdown.py -q`. T009–T012 must all
> fail with `AttributeError`. Do not proceed until they do.

- [x] **T013** [US2] In `src/wyrdbound_dice/roll_result.py`, add four static
  methods to `KeepOperationProcessor`: `apply_keep_operations_indexed`,
  `apply_drop_operations_indexed`, `apply_legacy_keep_indexed`, and a private
  `_sorted_pairs(rolls)` returning `sorted(enumerate(rolls), key=lambda p: p[1])`.
  Each mirrors its existing counterpart exactly but operates on `(index, value)`
  pairs and returns `(kept_indices, dropped_indices)` as lists of ints. **Do not
  modify the existing value-returning methods** — callers depend on them.
  *Accept:* `python -m pytest tests/ -q` unchanged.

- [x] **T014** [US2] Rewrite `RollResult._calculate_kept_and_dropped` to call the
  T013 methods, set `self.kept_indices` and `self.dropped_indices`, then derive
  `self.kept = [self.rolls[i] for i in sorted(self.kept_indices)]` and
  `self.dropped` likewise. `sum(self.kept)` must be unchanged for every corpus
  expression (rule 2).
  *Accept:* T012 passes; `python -m pytest tests/test_format_snapshots.py -q` green.

- [x] **T015** [US2] Add `dice_traces: Optional[List[dict]] = None` as the
  **last** keyword parameter of `RollResult.__init__` and store it. When `None`,
  synthesise one trace per entry of `self.rolls` as
  `{"faces": [v], "sources": ["roll"], "value": v}`, using `self.all_rolls` when
  its length equals `len(self.rolls)` and `self.rolls` otherwise. Docstring the
  synthesised form as a fallback for results built without tracing (flux results
  take this path).
  *Accept:* T009 passes.

- [x] **T016** [US2] In `src/wyrdbound_dice/dice.py`, inside
  `_roll_single_dice_expression`, build `dice_traces: List[dict]` alongside
  `all_rolls`. Create the list before the `for _ in range(num):` loop; at the top
  of each iteration create `trace = {"faces": [], "sources": [], "value": 0}`.
  Append `(face, "roll")` for the initial roll, `(face, "reroll")` inside **both**
  reroll `while` loops, and `(face, "explosion")` inside the explosion loop — at
  exactly the points where the existing code appends to `all_rolls`. After
  `rolls.append(current_total)`, set `trace["value"] = current_total` and append
  the trace. **`all_rolls` is not touched** (rule 3).
  *Accept:* T010 and T011 pass once T017 lands.

- [x] **T017** [US2] Pass `dice_traces=dice_traces` to the `RollResult(...)`
  constructor at the end of `_roll_single_dice_expression`.
  *Accept:* T010 and T011 pass.

- [x] **T018** [US2] Run `python -m pytest tests/ -q`, then `black`/`isort`/`ruff`
  over `src/ tests/ tools/`.
  *Accept:* T009–T012 green, snapshots green, quality checks clean.

**Checkpoint 2.** Per-phase gate. Patch bump.

---

## Phase 3 — The breakdown data model

**Purpose:** the structured types, built from `RollResult`. Still nothing
rendered changes.

- [x] **T019** [P] [US2] Append failing `test_breakdown_types_exist_and_are_frozen`
  to `tests/test_breakdown.py`: import `Die`, `DiceGroup`, `Literal`, `DiceNode`,
  `UnaryOp`, `BinaryOp`, `ModifierBreakdown`, `RollBreakdown` from
  `wyrdbound_dice.breakdown`; construct a minimal instance of each; assert
  `dataclasses.is_dataclass(obj)` and that assignment raises
  `dataclasses.FrozenInstanceError`.
  *Accept:* fails with `ImportError`.

- [x] **T020** [P] [US2] Append failing `test_roll_result_breakdown_shape`: roll
  `"4d6kh3"` seed 42; `g = result.results[0].breakdown`; assert
  `isinstance(g, DiceGroup)`, `g.num == 4`, `g.sides == "6"`,
  `g.kind == "standard"`, `len(g.dice) == 4`,
  `sum(1 for d in g.dice if not d.kept) == 1`, `g.keep_operations == (("h", 3),)`,
  and `g.subtotal == sum(d.value for d in g.dice if d.kept)`.
  *Accept:* fails with `AttributeError`.

- [x] **T021** [P] [US2] Append failing `test_breakdown_kinds`: `"4dF"` →
  `kind == "fudge"`; `"1d%"` → `"percentile"`; `"2d6"` → `"standard"`.
  *Accept:* fails with `AttributeError`.

- [x] **T022** [P] [US2] Append failing `test_breakdown_faces_match_all_rolls`:
  for `"3d6"`, `"2d6e"`, `"4dF"`, `"1d%"`, assert
  `[f for d in g.dice for f in d.faces] == r.all_rolls`.
  *Accept:* fails with `AttributeError`.

- [x] **T023** [P] [US2] Append failing `test_to_node_returns_dice_node`: for
  `"2d6"`, `isinstance(result.results[0].to_node(), DiceNode)`.
  *Accept:* fails with `AttributeError`.

> **Gate.** `python -m pytest tests/test_breakdown.py -q` — T019–T023 fail with
> `ImportError` or `AttributeError`.

- [x] **T024** [US2] Create `src/wyrdbound_dice/breakdown.py` with the
  dataclasses, the `Node` union alias and
  `PRECEDENCE = {"+": 1, "-": 1, "x": 2, "/": 2}` exactly as §3.2/§3.4 specify.
  All dataclasses `frozen=True`; sequence fields typed `Tuple[...]` with default
  `()`; imports limited to `dataclasses` and `typing`. Do **not** define
  `to_dict` yet — leave it out entirely rather than stubbing it.
  *Accept:* T019 passes.

- [x] **T025** [US2] Add a `breakdown` property to `RollResult` returning a
  `DiceGroup`. `kind` is `"fudge"` / `"percentile"` / `"standard"` from the flags;
  `notation` is `f"{num}d{sides}"` + `_build_keep_string()` + `_build_drop_string()`
  + `_build_reroll_string()` + `_build_explode_string()` **in that order** —
  verify against the corpus entry `"4d6r<=2kh3"`, which renders `4d6kh3r<=2`;
  `dice` is one `Die` per `dice_traces` entry with
  `kept=(i in set(self.kept_indices))`; `keep_operations`/`drop_operations` as
  tuples of tuples; `reroll` is `(reroll_count, reroll_cmp, reroll_target)` or
  `None`; `explode` is `(explode_cmp, explode_target)` or `None`;
  `subtotal=sum(self.kept)`; `total=(sum(self.kept) * multiply) // divide`.
  *Accept:* T020, T021, T022 pass.

- [x] **T026** [US2] Add `RollResult.to_node()` returning `DiceNode(self.breakdown)`.
  *Accept:* T023 passes.

- [x] **T027** [US2] Implement `RollBreakdown.to_dict()` and a module-private
  `_node_to_dict(node)` in `breakdown.py`. Each node dict carries a `"type"` key:
  `"literal"`, `"dice"`, `"unary"`, `"binary"`. Percentile faces serialise as
  two-element lists. No enums, tuples or dataclasses may survive into the output.
  *Accept:* T028.

- [x] **T028** [P] [US2] Append `test_to_dict_is_json_serialisable`: for
  `"4d6kh3"`, `"1d%"`, `"4dF"` and `"2d6 + 1d4 x 2 - 1"`, call
  `json.dumps(result.breakdown.to_dict())` and assert it does not raise. This
  depends on `RollResultSet.breakdown`, which lands at **T059** — mark it
  `@pytest.mark.xfail(reason="RollResultSet.breakdown lands in T059", strict=True)`
  now; **T060** removes the marker.
  *Accept:* the test xfails.

- [x] **T029** [P] [US2] In `src/wyrdbound_dice/__init__.py`, import and add to
  `__all__`: `RollBreakdown`, `DiceGroup`, `Die`, `ModifierBreakdown`, `Literal`,
  `DiceNode`, `UnaryOp`, `BinaryOp`.
  *Accept:* `python -c "import sys; sys.path.insert(0,'src'); from wyrdbound_dice import RollBreakdown, Die"`.

- [x] **T030** [US2] Run `python -m pytest tests/ -q` and `black`/`isort`/`ruff`.
  *Accept:* T019–T023 green, T028 xfails, snapshots green.

**Checkpoint 3.** Per-phase gate. Patch bump.

---

## Phase 4 — The formatter

**Purpose:** a complete, tested renderer built against **hand-constructed**
breakdown objects. No RNG, no evaluator changes, nothing wired into `__str__`.
Proving the renderer in isolation is what makes Phase 5 survivable.

- [x] **T031** [P] [US3] Create `tests/test_formatting.py` with a module
  docstring, imports from `wyrdbound_dice.breakdown` and
  `wyrdbound_dice.formatting`, and three helpers building breakdowns **by hand,
  with no dice rolls**: `simple_group()` — `2d6`, dice 6 and 2, all kept,
  subtotal 8; `keep_group()` — `4d6kh3`, dice 1 (dropped), 2, 5, 6;
  `fudge_group()` — `kind="fudge"`, raw faces 1, 3, 5.
  *Accept:* the file imports cleanly.

- [x] **T032** [P] [US3] Write failing `test_enums_exist`: `Dropped.SHOWN`,
  `.HIDDEN`, `.MARKED`, `Percentile.PAIR`, `.VALUE` all exist, with exactly 3 and
  2 members respectively.
  *Accept:* fails with `ImportError`.

- [x] **T033** [P] [US3] Write failing `test_rollformat_defaults`: every field of
  `RollFormat()` equals its §5 default, field by field, including
  `layout == "{total} = {breakdown}"`; `RollFormat()` is hashable and frozen.
  *Accept:* fails with `ImportError`.

- [x] **T034** [P] [US4] Write failing layout-validation tests:
  `RollFormat(layout="no placeholders")` raises `ValueError`;
  `RollFormat(layout="{total} {bogus}")` raises `ValueError` with a message
  naming `total`, `breakdown` and `expression`; `RollFormat(layout="{}")` raises
  `ValueError`; `RollFormat(layout="{total}")` and `RollFormat(layout="{expression}")`
  both construct cleanly.
  *Accept:* fails with `ImportError`.

- [x] **T035** [P] [US3] Write failing `test_format_group_standard`:
  `DefaultFormatter().format_group(simple_group()) == "8 (2d6: 6, 2)"`.
  *Accept:* fails with `ImportError`.

- [x] **T036** [P] [US3] Write failing `test_layout_arrangements` against a
  hand-built `RollBreakdown` with root
  `BinaryOp(DiceNode(simple_group()), "+", Literal(3), 11)`, `total=11`,
  `expression="2d6 + 3"`:

  | `layout` | Output |
  | --- | --- |
  | `"{total} = {breakdown}"` | `11 = 8 (2d6: 6, 2) + 3` |
  | `"{breakdown}"` | `8 (2d6: 6, 2) + 3` |
  | `"{total}"` | `11` |
  | `"{breakdown} => {total}"` | `8 (2d6: 6, 2) + 3 => 11` |
  | `"{expression}: {total}"` | `2d6 + 3: 11` |
  | `"[{total}] {breakdown}"` | `[11] 8 (2d6: 6, 2) + 3` |

  *Accept:* fails with `ImportError`.

- [x] **T037** [P] [US4] Write failing
  `test_layout_does_not_reparse_rendered_braces`: default layout,
  `dropped_marker="{{{value}}}"`, format `keep_group()`; assert literal braces
  appear in the output and nothing raises. This is rule 8.
  *Accept:* fails with `ImportError`.

  > **Note (maintainer decision, 2026-09-15).** The test is written and
  > committed. It cannot *pass* until `Dropped.MARKED` rendering lands at T075;
  > it carries a strict `xfail` marker until then, mirroring the T028/T060
  > pattern. **T075 must remove the marker.** T050's original accept named T037
  > — that is a forward reference and does not block T050.

- [x] **T038** [P] [US4] Write failing `test_precedence_parenthesisation` over
  hand-built trees: `BinaryOp(BinaryOp(Literal(2), "+", Literal(3), 5), "x", Literal(2), 10)`
  → `"(2 + 3) x 2"`; `BinaryOp(Literal(10), "-", BinaryOp(Literal(2), "x", Literal(3), 6), 4)`
  → `"10 - 2 x 3"`; `BinaryOp(Literal(10), "-", BinaryOp(Literal(2), "-", Literal(3), -1), 11)`
  → `"10 - (2 - 3)"`.
  *Accept:* fails with `ImportError`.

- [x] **T039** [P] [US4] Write failing `test_glyph_overrides`: `multiply_symbol="×"`
  renders `×` and no `x`; `die_separator=" "` → `"8 (2d6: 6 2)"`;
  `group_open="["`/`group_close="]"` → `"8 [2d6: 6, 2]"`; `show_notation=False`
  → `"8 (6, 2)"`.
  *Accept:* fails with `ImportError`.

- [x] **T040** [P] [US4] Write failing `test_fudge_symbols`: `fudge_group()`
  renders `"-, B, +"` by default and `"-, 0, +"` with
  `fudge_symbols=("-", "0", "+")`.
  *Accept:* fails with `ImportError`.

- [x] **T041** [P] [US4] Write failing `test_percentile_styles`: a hand-built
  percentile group with face `(60, 0)` renders `"[60, 0]"` under
  `Percentile.PAIR` and `"60"` under `Percentile.VALUE`.
  *Accept:* fails with `ImportError`.

- [x] **T042** [P] [US4] Write failing `test_zero_dice_group`: a `DiceGroup` with
  `num=0` and no dice renders `"0 (0d6)"` — no trailing separator, no empty
  bracket contents.
  *Accept:* fails with `ImportError`.

- [x] **T043** [P] [US6] Write failing `test_formatter_protocol_and_subclass`: a
  `DefaultFormatter` subclass overriding `format_die` to return `"#"` renders
  every die as `#`; a plain object with a `format(self, breakdown)` method
  satisfies `isinstance(obj, Formatter)`.
  *Accept:* fails with `ImportError`.

> **Gate.** `python -m pytest tests/test_formatting.py -q` — T032–T043 all fail
> with `ImportError`.

- [x] **T044** [US3] Create `src/wyrdbound_dice/formatting.py` with the `Dropped`
  and `Percentile` enums and the frozen `RollFormat` dataclass exactly as §5
  specifies, including `layout`. Imports limited to `dataclasses`, `enum`,
  `typing`, `.breakdown`. **Do not define presets yet** — they land at T068.
  *Accept:* T032 and T033 pass.

- [x] **T045** [US4] Add `RollFormat.__post_init__` validating `layout`: attempt
  `self.layout.format(total="", breakdown="", expression="")`, converting
  `KeyError`, `IndexError` or `ValueError` into
  `ValueError("layout may only use {total}, {breakdown} and {expression}; got: …")`;
  then require at least one of the three placeholders. The method **only reads
  `self`** — never assigns — so `frozen=True` is preserved.
  *Accept:* T034 passes.

- [x] **T046** [US6] Add the `Formatter` protocol (`typing.Protocol`, decorated
  `@runtime_checkable`) with a single `format(self, breakdown: RollBreakdown) -> str`.
  *Accept:* the second half of T043 passes.

- [x] **T047** [US3] Implement `DefaultFormatter.__init__`, `format_die` and
  `format_group`. `format_die`: for `kind == "fudge"` map each raw face through
  `fudge_symbols` at the existing thresholds (`<= 2` → 0, `<= 4` → 1, else 2);
  for `"percentile"` render `f"[{tens:02d}, {ones}]"` under `PAIR` — matching
  `_format_rolls_display` exactly, **including the `if tens < 100` guard** — or
  `str(value)` under `VALUE`; otherwise `str()` each face. Join a die's faces with
  `die_separator`. `format_group` renders
  `f"{total}{group_open}{notation}{notation_separator}{dice}{group_close}"`,
  joining dice with `die_separator`, omitting the notation and its separator when
  `show_notation` is False, and omitting the whole bracketed section when the
  group has no dice.
  *Accept:* T035, T039, T040, T041, T042 and the first half of T043 pass.

- [x] **T048** [US3] Implement `DefaultFormatter.format_node(node, parent_precedence=0)`
  for `Literal`, `DiceNode`, `UnaryOp`, `BinaryOp`. Use `breakdown.PRECEDENCE`:
  wrap a `BinaryOp` child when `PRECEDENCE[child.op] < PRECEDENCE[parent.op]`, or
  when equal and the child is the **right** operand of `-` or `/`. Substitute
  `multiply_symbol` for `"x"` and `divide_symbol` for `"/"` at render time.
  Binary operators are surrounded by single spaces; `UnaryOp` renders with no
  space (`-4`).
  *Accept:* T038 passes.

- [x] **T049** [US3] Implement `DefaultFormatter.format_modifier(modifier)`
  honouring `modifier_depth`: `0` → `f"{sign} {abs(value)}"`; `1` →
  `f"{sign} {abs(value)} ({name})"`, omitting the parenthesised part when `name`
  is empty; `2` → as `1` for a static modifier, and for a dice modifier
  `f"{sign} {abs(value)} ({name}: {nested})"` where `nested` is this formatter
  applied to `modifier.nested` with the **same** `layout`, so a custom
  arrangement applies at every depth. Reference output: the corpus entry
  `("1d20", {"Bless": "1d4"})` renders the modifier as
  `+ 1 (Bless: 1 = 1 (1d4: 1))`.
  *Accept:* rendering a hand-built dice modifier matches that string.

- [x] **T050** [US3] Implement `DefaultFormatter.format(breakdown)`: if
  `"{breakdown}"` appears in the layout, render the root via `format_node` and
  append each modifier rendered by `format_modifier`, separated by single spaces,
  to form the body; otherwise skip that work entirely and use `""`. Return
  `self.fmt.layout.format(total=str(breakdown.total), breakdown=body, expression=breakdown.expression)`.
  *Accept:* T036 and T037 pass.

- [x] **T051** [P] [US3] In `src/wyrdbound_dice/__init__.py`, import and add to
  `__all__`: `RollFormat`, `Dropped`, `Percentile`, `Formatter`, `DefaultFormatter`.
  *Accept:* `python -c "import sys; sys.path.insert(0,'src'); from wyrdbound_dice import RollFormat, DefaultFormatter"`.

- [x] **T052** [US3] Run `python -m pytest tests/ -q` and `black`/`isort`/`ruff`.
  *Accept:* T032–T043 green; snapshots green (nothing is wired yet).

**Checkpoint 4.** Per-phase gate. Patch bump.

---

## Phase 5 — The tree-returning evaluator

**Purpose:** replace string-built descriptions with the evaluated tree and route
`__str__` through the formatter. **This is the risky phase.** Read §1, §4.1 and
the green-snapshot trap before starting. Re-run the snapshot suite after every
task here, not only at the end.

- [x] **T053** [US1] In `expression_parser.py`, change `EvaluationResult` to
  `value: int`, `node: Node`, `dice_results: List[RollResult]`, and add a
  `description` property returning
  `DefaultFormatter(RollFormat(layout="{breakdown}")).format_node(self.node)`.
  Import from `.breakdown` and `.formatting`. **Do not delete `DescriptionBuilder`
  yet.**
  *Accept:* the module imports; `python -m pytest tests/ -q` still green.

  > **Merged with T054 (maintainer decision, 2026-09-15).** T053 cannot pass its
  > gate alone: replacing the `description` field with a property breaks the four
  > `evaluate()` methods that still pass `description=`. The two landed as one
  > green commit.

- [x] **T054** [US1] Update the four `evaluate()` methods to build nodes instead
  of strings: `NumberExpression` → `Literal(self.value)`; `DiceExpression` →
  `result.to_node()`; `BinaryOperation` →
  `BinaryOp(left.node, op_symbol, right.node, value)`; `UnaryOperation` →
  `UnaryOp("-", operand.node, value)`. Stop passing `description=` anywhere.
  *Accept:* the module imports and no call site passes `description=`.

- [x] **T055** [US1] Delete `DescriptionBuilder` from `expression_parser.py`
  entirely, along with its now-unused imports. Run
  `python -m pytest tests/test_format_snapshots.py -q`.

  **This will fail, and that is the point.** Produce the complete list of failing
  keys with expected and actual strings. If the list contains anything beyond
  expressions whose v0.0.3 rendering drops user-written parentheses or adds
  redundant ones (§1a, §4.1), **stop** — something else changed. If the list is
  limited to those, **stop and get maintainer sign-off** before T056. Rule 1
  applies: do not regenerate the snapshot file on your own authority.
  *Accept:* the failure list is produced and sign-off is recorded in the commit
  message or an issue link.

  > **Sign-off recorded (maintainer, 2026-09-15).** `DescriptionBuilder` is
  > deleted. The failure list is exactly five entries, all §4.1:
  >
  > | Entry | v0.0.3 | new |
  > | --- | --- | --- |
  > | snapshot `(2d6 + 3) x 2 + 1d4 - 1` | `17 = 5 (2d6: 4, 1) + 3 x 2 + 2 (1d4: 2) - 1` | `17 = (5 (2d6: 4, 1) + 3) x 2 + 2 (1d4: 2) - 1` |
  > | snapshot `10 - 2 x 3` | `4 = 10 - (2 x 3)` | `4 = 10 - 2 x 3` |
  > | `test_mixed_operations_wrong_precedence_bug` | `62 = 6 (2d6: 1, 5) + (7 x 4) x 2` | `62 = 6 (2d6: 1, 5) + 7 x 4 x 2` |
  > | `test_complex_math_expression_parsing_bug` | `5 = 14 (2d8: 6, 8) - 5 (1d6: 5) - (1 x 4)` | `5 = 14 (2d8: 6, 8) - 5 (1d6: 5) - 1 x 4` |
  > | `test_order_of_operations_division_in_complex_expression` | `9 = 11 (2d10: 7, 4) - (7 / 4) - 1 (1d4: 1)` | `9 = 11 (2d10: 7, 4) - 7 / 4 - 1 (1d4: 1)` |
  >
  > All five are the §1a defect: parentheses dropped where the user wrote them,
  > or added where precedence already implies them. Every total is unchanged.
  > An earlier draft of this refactor also lost the legacy `A + -B` → `A - B`
  > sign normalisation (two further diffs, `4dF + 4dF` and `-4dF`); that was
  > restored in the formatter before sign-off, so it is **not** in this list.
  > The three `unittest` assertions above are updated to the new output at T056
  > with maintainer approval; they are not weakened — the totals are identical.

- [x] **T056** [US1] *(Only after T055 sign-off.)* Run
  `python tools/gen_format_snapshots.py`, then `git diff` the snapshot file and
  keep the diff — **T081** pastes it into `CHANGELOG.md`. Re-run
  `python -m pytest tests/ -q`.
  *Accept:* the suite is green and the diff is saved for T081.

- [x] **T057** [US1] In `dice.py`, add `self._root: Optional[Node] = None` to
  `RollResultSet.__init__` and delete `self._override_description`. In
  `_parse_with_precedence`, set `result_set._root = result.node` and delete both
  assignments to `_override_description`.
  *Accept:* `grep -rn "_override_description" src/` returns nothing.

- [x] **T058** [US1] Delete the dead `_has_leading_zero_minus` branch from
  `RollResultSet._build_formula_parts` (§9.2). Confirm with
  `grep -rn "_has_leading_zero_minus" src/ tests/ tools/` **before** deleting.
  *Accept:* the grep returns nothing afterwards; snapshots green.

- [x] **T059** [US2] Add a `breakdown` property to `RollResultSet` returning a
  `RollBreakdown`. Use `self._root` when set. When it is `None` — the legacy
  `_roll_original_method` path — build the root by left-folding `self.results`:
  start from `results[0].to_node()`, then append each subsequent result as
  `BinaryOp(acc, "+", node, value)`, or `"-"` with the operand's sign flipped
  when that result's total is negative, reproducing what `_build_formula_parts`
  produced. Build `modifiers` from `self.modifiers`, setting
  `nested=m.dice_result.breakdown` when `m.is_dice`.
  *Accept:* T060.

  > **Merged with T060 (maintainer decision, 2026-09-15).** T028's strict
  > `xfail` turns into an `XPASS` failure the moment T059 lands, so T059 cannot
  > be green with the marker still present. Both landed in one commit.

- [x] **T060** [US2] Remove the `xfail` marker added at T028.
  *Accept:* `test_to_dict_is_json_serialisable` passes.

- [x] **T061** [US1] Reimplement `RollResultSet.__str__` as
  `DefaultFormatter(RollFormat()).format(self.breakdown)` and delete
  `_build_formula_parts`. (T068 switches this to `RollFormat.STANDARD`; they are
  equal by construction.) **It must not read the module default** (rule 7).
  *Accept:* snapshots green.

  > **Merged with T062 and T063 (maintainer decision, 2026-09-15).** Routing the
  > set through `breakdown` bypasses the two flux `__str__` overrides, so
  > `GOODFLUX`/`BADFLUX` go red the moment T061 lands; T063 replaces those
  > overrides with `to_node`. T062's rewrite of `RollResult.__str__` is
  > inseparable from its deletion of the four dead renderers. The three landed
  > as one commit and the suite is green.

- [x] **T062** [US1] Reimplement `RollResult.__str__` as
  `DefaultFormatter(RollFormat(layout="{breakdown}")).format_node(self.to_node())`.
  Delete `_format_rolls_display`, `_build_cross_dice_string`,
  `_build_math_operation_string` and the `FudgeDiceFormatter` class. **Keep**
  `_build_keep_string`, `_build_drop_string`, `_build_reroll_string` and
  `_build_explode_string` — `breakdown` uses them. If `_build_cross_dice_string`
  turns out to be reachable for any corpus expression, stop and report: that is a
  gap in this plan, not a decision for you.
  *Accept:* snapshots green.

  > **Reachability checked.** `_cross_dice_op` and `_cross_dice_result` are
  > assigned `None` in `__init__` and never set non-`None` anywhere in `src/`,
  > `tests/` or `tools/`, so `_build_cross_dice_string` was already dead. The
  > stop condition did not trigger. A `divide == 0` guard that lived in the old
  > `RollResult.__str__` was moved into the `breakdown` property so
  > `DivisionByZeroError` still fires exactly as before.

- [x] **T063** [US1] Delete `GoodFluxResult.__str__` and `BadFluxResult.__str__`,
  and override `to_node()` on each to return
  `BinaryOp(DiceNode(first_group), "-", DiceNode(second_group), value)` where each
  group is a synthetic
  `DiceGroup(num=1, sides="6", kind="standard", notation="1d6", dice=(Die(value=v, faces=(v,), sources=("roll",), kept=True),), subtotal=v, total=v)`.
  `GoodFluxResult` puts the **high** group first; `BadFluxResult` the **low**.
  Reference: at seed 42 `GOODFLUX` renders `3 = 4 (1d6: 4) - 1 (1d6: 1)` and
  `BADFLUX` renders `-3 = 1 (1d6: 1) - 4 (1d6: 4)`.
  *Accept:* both corpus entries match.

- [x] **T064** [US1] Run `python -m pytest tests/ -q` and `black`/`isort`/`ruff`.
  *Accept:* everything green; six renderers are now one.

**Checkpoint 5.** Per-phase gate. Patch bump.

---

## Phase 6 — Presets and the module default

- [x] **T065** [P] [US3] Write failing `test_presets_exist` and
  `test_standard_equals_default`: `RollFormat.STANDARD`, `.COMPACT`, `.MINIMAL`,
  `.VERBOSE` exist and are `RollFormat` instances; `RollFormat.STANDARD == RollFormat()`.
  *Accept:* fails with `AttributeError`.

- [x] **T066** [P] [US3] Write failing `test_presets_render`: roll `"4d6kh3"` at
  seed 42 (corpus value `8 = 8 (4d6kh3: 4, 1, 2, 2)`); assert
  `result.format(RollFormat.STANDARD) == str(result)`,
  `result.format(RollFormat.MINIMAL) == "8"`, and
  `result.format(RollFormat.VERBOSE) != str(result)`.
  *Accept:* fails with `AttributeError`.

- [x] **T067** [P] [US5] Write failing module-default tests, with a `yield`
  fixture calling `set_default_format(None)` on teardown so no test leaks state:
  unset → `get_default_format() == RollFormat.STANDARD`; after
  `set_default_format(RollFormat.COMPACT)`, `result.format()` equals
  `result.format(RollFormat.COMPACT)`; `str(result)` is **unchanged** while a
  default is set (rule 7); `set_default_format(None)` restores STANDARD.
  *Accept:* fails with `ImportError`.

> **Gate.** T065–T067 all fail.

- [ ] **T068** [US3] Assign the four presets as class attributes on `RollFormat`
  after the class body, exactly as §5 gives them. Switch T061's `RollFormat()` to
  `RollFormat.STANDARD`.
  *Accept:* T065 and T066 pass; snapshots green.

- [ ] **T069** [US5] Add module-private `_DEFAULT_FORMAT: Optional[RollFormat] = None`
  plus `set_default_format(fmt)` and `get_default_format()`, the latter returning
  `RollFormat.STANDARD` when unset. Docstrings must state that this is display
  state read only at render time, that it does not affect `__str__`, and that it
  is intended to be set once at application startup.
  *Accept:* the first and last assertions of T067 pass.

- [ ] **T070** [US5] Add `RollResultSet.format(fmt=None)`: `None` →
  `get_default_format()`; a `RollFormat` → `DefaultFormatter(fmt).format(self.breakdown)`;
  anything else carrying a `format` attribute → `fmt.format(self.breakdown)`.
  Never raises for a successfully-evaluated result; never rolls a die.
  *Accept:* T066 and T067 pass in full.

- [ ] **T071** [P] [US5] Add `set_default_format` and `get_default_format` to the
  imports and `__all__` in `src/wyrdbound_dice/__init__.py`.
  *Accept:* both import from the package root.

- [ ] **T072** [US5] Run `python -m pytest tests/ -q` and `black`/`isort`/`ruff`.
  *Accept:* all green.

**Checkpoint 6.** Per-phase gate. Patch bump.

---

## Phase 7 — Dropped dice and reroll display

**Purpose:** the first tasks that change what a user can see — reachable only
through non-default formats, which is why this is a MINOR bump and not a MAJOR one.

- [ ] **T073** [P] [US4] Write failing dropped-display tests against
  `keep_group()`: `Dropped.SHOWN` renders all four dice (default, unchanged);
  `Dropped.HIDDEN` renders only the three kept; `Dropped.MARKED` renders the
  dropped die as `~1~` and the kept dice unmarked; `dropped_marker="[{value}]"`
  produces `[1]`.
  *Accept:* fails.

- [ ] **T074** [P] [US4] Write failing `test_show_rerolls_false`: a hand-built
  `DiceGroup` with one die whose `faces=(1, 5)` and `sources=("roll", "reroll")`
  renders both faces by default and only `5` with `show_rerolls=False`.
  *Accept:* fails.

> **Gate.** T073 and T074 fail.

- [ ] **T075** [US4] Extend `format_die` and `format_group` to honour `dropped`
  and `show_rerolls`. `HIDDEN` omits a die entirely when `die.kept` is False.
  `MARKED` wraps that die's rendered text with `dropped_marker.format(value=<rendered>)`.
  `show_rerolls=False` renders only the die's final face for a rerolled die, but
  **still renders every `"explosion"` face**, because they all contribute to the
  value. Document that asymmetry in the method docstring — it is the kind of rule
  that looks like a bug six months later.
  *Accept:* T073 and T074 pass, and the strict `xfail` marker on
  `test_layout_does_not_reparse_rendered_braces` (added with T037) is removed so
  the test passes for real.

- [ ] **T076** [US4] Run `python -m pytest tests/ -q` and `black`/`isort`/`ruff`.
  *Accept:* snapshots **still green** — `SHOWN` and `show_rerolls=True` are the
  defaults, so STANDARD output is untouched.

**Checkpoint 7.** Per-phase gate. Patch bump.

---

## Phase 8 — CLI, docs, and the gate

- [ ] **T077** [P] [US7] In `tools/roll.py`, add `--format` with
  `choices=["standard", "compact", "minimal", "verbose"]` defaulting to
  `"standard"`, and `--detail` as `store_true`. Map the choice to the preset via a
  module-level dict and use `result.format(preset)` for text output.
  *Accept:* `python tools/roll.py "4d6kh3" --seed 42 --format minimal` prints only
  the total.

- [ ] **T078** [P] [US7] In `tools/roll.py`, when `--json` **and** `--detail` are
  both set, add `"breakdown": result.breakdown.to_dict()` to each roll's dict.
  Without `--detail`, the JSON keys are exactly what v0.0.3 emitted.
  *Accept:* T079.

- [ ] **T079** [US7] Create `tests/test_cli_format.py` driving `tools/roll.py`
  through `subprocess.run([sys.executable, "tools/roll.py", ...])`: `--seed 42 --json`
  keys are exactly `{"result", "description", "seed"}`; `--seed 42 --json --detail`
  additionally has `breakdown`; `--format minimal` prints only the total; exit
  code 0 in each case.
  *Accept:* `python -m pytest tests/test_cli_format.py -q`.

- [ ] **T080** [P] [US7] Add a "Formatting Roll Output" section to `README.md`
  after "RNG Injection": presets, `result.format()`, field overrides with
  `dataclasses.replace`, the `layout` template with its three placeholders and its
  construction-time validation, `set_default_format`, the structured breakdown
  with a `to_dict()` example, custom `Formatter` subclassing, and the new CLI
  flags. Every example must be runnable and its output correct at seed 42.
  *Accept:* every README example produces the output it claims.

- [ ] **T081** [P] Update `CHANGELOG.md` under `[Unreleased]`: one `feat:` line
  for configurable roll formatting and the structured breakdown, one `feat:` line
  for the CLI flags, and — if T056 ran — one `fix:` line for precedence-correct
  parenthesisation including the enumerated renderings from the T056 diff.
  Conventional Commits, lowercase after `type: `, no bullet lists inside the
  description.
  *Accept:* the entry names every changed rendering.

- [ ] **T082** [P] Update `AGENTS.md` §Architecture to list `breakdown.py` and
  `formatting.py` with one-line purposes, and note that all rendering flows
  through `DefaultFormatter`.
  *Accept:* the architecture block matches the tree on disk.

- [ ] **T083** Add docstrings to every public class, method and function added by
  this feature that lacks one.
  *Accept:* `ruff check src/ tests/ tools/` clean.

- [ ] **T084** Verify the Python 3.8 floor:
  `grep -rn "list\[\|dict\[\|tuple\[\|set\[\| | None\|slots=True" src/wyrdbound_dice/`
  returns nothing. If `python3.8` is available, run
  `python3.8 -c "import sys; sys.path.insert(0, 'src'); import wyrdbound_dice"`.
  *Accept:* the grep is empty.

- [ ] **T085** Final gate: `python -m pytest tests/ -q --cov=wyrdbound_dice`, then
  `black src/ tests/ tools/`, `isort src/ tests/ tools/`,
  `ruff check src/ tests/ tools/`. Confirm no file under `tests/` differs from its
  state at T007 except the new test files — and `tests/data/format_snapshots.json`
  only if T056 ran with sign-off.
  *Accept:* everything green; `git diff --stat` over `tests/` shows only expected
  files.

- [ ] **T086** Manual CLI check (`AGENTS.md` review checklist): run
  `python tools/roll.py "4d6kh3" --seed 42`, `… --format minimal`,
  `… --format verbose`, `… --json --detail`, and
  `python tools/roll.py "GOODFLUX" --seed 42`. Bump the **minor** version in
  `pyproject.toml` and `src/wyrdbound_dice/__init__.py:__version__`.
  *Accept:* every command's output is sensible and the two version strings match.

**Checkpoint 8 — the list is done.**

---

## Execution order

| Phase | Tasks | Gate | User-visible? |
| --- | --- | --- | --- |
| 1 — The characterization net | T001–T007 | Checkpoint 1 | No |
| 2 — Per-die provenance | T008–T018 | Checkpoint 2 | No |
| 3 — The breakdown data model | T019–T030 | Checkpoint 3 | No |
| 4 — The formatter | T031–T052 | Checkpoint 4 | No |
| 5 — The tree-returning evaluator | T053–T064 | Checkpoint 5 | Parenthesis fixes only, signed off |
| 6 — Presets and the module default | T065–T072 | Checkpoint 6 | Opt-in only |
| 7 — Dropped dice and reroll display | T073–T076 | Checkpoint 7 | Opt-in only |
| 8 — CLI, docs, and the gate | T077–T086 | Checkpoint 8 | Additive flags |

Phases are strictly sequential: each touches files the next one depends on.
Phase 4 is the largest and the safest — it builds and proves the renderer against
hand-built data, so that Phase 5, which is the dangerous one, changes only where
the renderer is called from and not what it does.

---

## Deferred, and why each is out

| Deferred | Why | Where it lands |
| --- | --- | --- |
| ANSI, Markdown or Rich output | Each adds a styling vocabulary to `RollFormat` and a correctness burden — escaping, width, nesting — with no clear stopping point, in a library whose primary consumer has its own presentation layer. §10. | Consumer side, over the breakdown; `DefaultFormatter` is subclassable precisely for this |
| Per-die and per-group templates | A genuine second level of templating, and unnecessary until someone wants a shape the typed options cannot express. Composes cleanly on top of `RollFormat` if demand appears; nothing here forecloses it. | A later slice, if asked for |
| `__format__` sugar — `f"{result:compact}"` | Charming, limits the format to one identifier, hides a lookup table behind a string. Pure addition over presets. | Any time, cheaply |
| §9.1 — `DiceExpression.evaluate()` reports `subtotal`, not the multiply/divide-adjusted total | Unresolved whether it is intentional. Changing it moves totals, which is the one thing this feature must not do (rule 2). The tree refactor puts the two adjacent and will force the question. | Its own change, with its own decision |
| §9.3 — `1d6e<=0` does not raise | `validate_explosion_condition` does not fire on an always-true condition. Fixing it changes which expressions raise. Pinned by a corpus entry so it cannot drift unnoticed. | Its own change |
| `{subtotal}` as a fourth layout placeholder | Trivial to add, no demonstrated use. Adding placeholders is cheap; removing them is not. | When something wants it |
| A formatting parameter on `Dice.roll()` | Five parameters already, and a result should be renderable many ways after the fact. §6. | Not planned |

---

## Input gaps to close before starting

1. **The FR-001a sign-off at T055.** The parenthesis fix is the one deliberate
   change to default output. **Decide before Phase 5 begins** who signs it off and
   where that is recorded — a commit message trailer or an issue link. An agent
   that reaches T055 without knowing this has two bad options and will pick the
   fast one.

2. **Whether `{expression}` earns its place in `layout`.** It costs nothing —
   `RollBreakdown.expression` already exists — and gives `"{expression}: {total}"`
   → `2d6 + 3: 17`. If it is not wanted, drop it from T034, T036, T045 and T050
   before starting; retrofitting a placeholder later is additive, removing one is
   a breaking change.

3. **Whether `COMPACT` should hide dropped dice.** As specified in §5 it sets
   `dropped=Dropped.HIDDEN`, so `4d6kh3` renders `8 (4d6kh3:4,2,2)` — compact, and
   silently different from every other preset about what the dice were. The
   alternative is `SHOWN`, which is longer but never surprises. Confirm at T068;
   it is a one-line change there and a documented behaviour change afterwards.

---

_Version: 0.1 | Last updated: 2026-09-15_
