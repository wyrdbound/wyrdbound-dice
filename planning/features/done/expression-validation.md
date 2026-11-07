# Expression Validation — one grammar, checked before any die is rolled

**Status:** Complete; unreleased (0.3.0). Tasks in `expression-validation-tasks.md`.
**Asked for by:** Wyrdbound (`planning/features/02-spec-findings.md` F27 in the
wyrdbound repository): a system loader must reject a malformed dice expression
at load, not on the first roll mid-session, and must do so without drawing
randomness.

---

## 1. Problem

There is no way to ask "is this a valid dice expression?" without rolling it.
The obvious workaround — roll with a fixed `rng` and discard the result — is not
a validator: with a constant source, `1d8r<5` rolls 1 forever and raises
`InfiniteConditionError`, and any real source draws randomness a caller may be
forbidden to draw.

Building the validator exposed three defects in `roll()` itself. Each makes
`roll()` accept or mis-evaluate input silently, so a validator built on it
would inherit them.

### (a) A dice count of two or more digits is lexed as a number

`ExpressionLexer._handle_digit_token` decides "dice or number" by peeking one
character: `self.peek() == "d"`. For `10d6` the next character after `1` is
`0`, so `10` becomes a NUMBER and the `d` an invalid character. Every
expression with a multi-digit count and an operator therefore fails the
precedence parser and falls back to the original method (b). With every die
showing 4:

```
10d6 - 10d6   → 80   (should be 0: subtraction became addition)
10d6 + 3      → 40   (should be 43: the modifier was dropped)
```

This is a correctness bug (Article IV) in the released v0.1.0.

### (b) The fallback discards whatever it does not understand

`roll_with_precedence` catches a precedence-parser `ParseError` and falls back
to `_roll_original_method`, which finds dice with a regex and sums them,
ignoring every other character. The original method is also used directly for
expressions without arithmetic. So all of these roll without complaint:

```
2d6 banana      1d20+{{ x }}      2d6+3 # note      1d6 + 1d6 + zz      3d6 5d8
```

`1d20+{{ x }}` is the case that matters to Wyrdbound: an unrendered template
rolls a plain d20. This violates Article VI — errors must be clear, never
silent — and the constitution's "validate and sanitize all user input".

### (c) Flux shorthands swallow the rest of the expression

`process_shorthands` returns the flux marker if `GOODFLUX` or `BADFLUX`
appears **anywhere**, so `GOODFLUX + 3` and `GOODFLUX banana` roll plain flux.

### (d) Two different shorthands keep only the last

Each shorthand was expanded into a fresh copy of the *uppercased original*, so
`FUDGE + BOON` became `FUDGE + 3d6kh2` — the fallback then happened to rescue
it by expanding again — and any shorthand uppercased the rest of the
expression (`FUDGE + 1d6` → `4dF + 1D6`). Found while writing T005.

### (e) The lexer never learned forms the fallback covered for

Also found in T005, once the fallback was gone: the precedence lexer rejected
percentile sides (`1d%`), drop modifiers (`4d6dh1`), and the whitespace the
dice-term grammar allows inside keep/drop (`4d6 dh 3`, `2d20 dl 1`); and a term
ending right after `r` or `k` (`1d6r`, `2d6k`) raised `TypeError` from
`None in "=<>"`. All of these reached the original method through the
fallback, so they rolled — or, for `1d6r`, silently rolled `1d6`.

## 2. What already exists

- `DiceExpressionValidator.validate_expression_input` — regex checks for
  malformed patterns; run on the precedence path and inside the original
  method.
- `validate_total_dice` — the pre-flight dice count.
- The per-term checks at the top of `_roll_single_dice_expression`: dice count
  and die size limits, fudge-with-reroll, and the infinite reroll/explode
  conditions. They run before any die is rolled, but only during a roll.
- The precedence lexer and parser, which already reject invalid characters
  correctly — their errors are simply thrown away by (b).

## 3. The model

**One pre-flight, shared by `roll()` and `validate()`.** Every check that does
not need a die result runs, in order, before anything is rolled:

1. length limit; Unicode normalisation;
2. shorthand expansion — every shorthand, as a whole word, case-insensitive,
   leaving the rest of the expression as written; a flux shorthand must be the
   whole expression;
3. the total-dice pre-flight;
4. negative-dice rewriting and `validate_expression_input`;
5. **the grammar gate**: the whole expression is tokenised and parsed by the
   precedence parser, for *every* expression, including the ones the original
   method will evaluate;
6. every DICE token is matched by `_dice_re` **in full** (a partial match is an
   error, not a shorter term) and passes the per-term checks.

`roll()` runs the pre-flight, then evaluates by the same path it uses today
(original method for simple expressions, precedence evaluator otherwise), with
no fallback. `validate()` runs the pre-flight and returns. Because they share
it, "`validate(e)` passes" means exactly "`roll(e)` will not raise a
`ParseError` or `InfiniteConditionError`". There is no second parser to drift.

Evaluation output is unchanged: the original method still evaluates the
expressions it evaluated before, so `STANDARD` output and the format snapshots
are byte-identical for every expression that was valid.

## 4. Public surface

```python
Dice.validate(expr: str) -> None
wyrdbound_dice.validate(expr: str) -> None
```

Raises `ParseError` or `InfiniteConditionError` with the same message `roll()`
would. Draws no randomness and rolls no dice. It raises `DivisionByZeroError`
only for a divisor that contains no dice and is zero (`1d6 / 0`,
`2d6 / (3 - 3)`), which fails on every roll; the pre-flight checks this, so
`roll()` raises it before rolling too. Whether `1d6 / (1d2 - 1)` divides by
zero depends on the dice, so that can only be found by rolling.

CLI (Article II): `tools/roll.py EXPR --check` validates instead of rolling —
exit 0 and `valid` (or `{"valid": true}` under `--json`); exit 1 with the error
on stderr (or `{"valid": false, "error": "…"}` under `--json`).

## 5. Constitution check

- **I** — no new dependency; a standalone public function.
- **II** — `--check` on the CLI, with `--json`.
- **III** — every task is test-first.
- **IV** — (a) fixes wrong totals; same seed still gives the same result.
- **V** — shorthands and modifiers keep their meaning; flux stands alone.
- **VI** — silent acceptance becomes a clear `ParseError`.

## 6. Decisions

- **D1 — Whitespace-separated dice are an error.** `3d6 5d8` summed both
  terms. Nothing documents or tests it, and it is indistinguishable from a
  missing operator. It now raises; write `3d6 + 5d8`.
- **D2 — No fallback.** After (a), the only expressions the precedence parser
  rejected but the original method accepted were ones with ignored text.
- **D3 — `validate()` never rolls.** Not even with a synthetic source; every
  check is static.
- **D4 — Minor bumps: 0.2.0, then 0.3.0.** Input that rolled before now raises, and totals
  change for multi-digit-count arithmetic (0.2.0, Checkpoint 1); `validate` and
  `--check` are new public API (0.3.0, Checkpoint 2).

## 7. What this is not

Not a new grammar, not a change to what any valid expression means, and not a
change to rendered output for any valid expression.
