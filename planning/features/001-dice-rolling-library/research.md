# Research: RNG Injection for Dice Rolling Library

**Feature**: addRNGInjection  
**Date**: 2026-05-03  
**Status**: Complete — all unknowns resolved

---

## Decision 1: Duck-Typed RNG Protocol Contract

**Decision**: Accept any object with a `random() -> float` method returning a value in `[0.0, 1.0)`. No base class, ABC, or registration required.

**Rationale**: Python's stdlib `random.Random` exposes `random()` as its core primitive — all other methods (`randint`, `uniform`, `choice`) are implemented on top of it. By accepting only `random()`, callers can pass `random.Random()`, `numpy.random.Generator` (via a thin wrapper), or a mock object with a single method. This is the lowest-friction duck-typed contract possible.

**Alternatives considered**:
- Accepting `randint(a, b)` directly: Rejected — `random.Random.randint()` is a higher-level convenience, and accepting it would make the contract harder to satisfy with mocks and numpy-style generators.
- Accepting a `Callable[[], float]`: Would work but loses the ability to pass `random.Random()` directly without wrapping. `random.Random` has `random()` as a method; a bare callable wouldn't carry state (seed) along with it.
- Formal Protocol/ABC: Rejected as over-engineering for a library this size. Duck typing is idiomatic Python and consistent with the existing `logger=` pattern.

---

## Decision 2: `randint(a, b)` Derivation from `random()`

**Decision**: Introduce a module-private helper `_randint(rng, a, b) -> int` in `dice.py`:

```python
def _randint(rng, a: int, b: int) -> int:
    if rng is None:
        return random.randint(a, b)
    return int(rng.random() * (b - a + 1)) + a
```

All three `DiceRoller` roll methods replace their `random.randint()` calls with `_randint(rng, ...)`.

**Rationale**: For dice sides ≤ 100 (and d100 at most), the bias from `int(random() * n)` is negligible (maximum bias < 1/2^53 per roll). The stdlib's own `randbelow` uses rejection sampling for cryptographic correctness, but that's not required here. This keeps the implementation trivially simple and dependency-free.

**Alternatives considered**:
- Rejection sampling like stdlib: More correct but adds ~15 lines of code for a bias so small it will never affect any game. Rejected.
- Requiring `randint` on the rng object: Would break clean mocking (`Mock(random=lambda: 0.5)`) and numpy compatibility. Rejected.

---

## Decision 3: Propagation Strategy Through Call Chain

**Decision**: Thread `rng` as an explicit keyword argument through every method in the call chain. No global/thread-local state.

**Call chain changes (outer → inner)**:

```
Dice.roll(expr, modifiers, debug, logger, rng=None)
  └─ Dice.roll_with_precedence(expr, modifiers, rng=None)
       ├─ Dice._roll_original_method(expr, modifiers, rng=None)
       │    └─ RollResultSet(results, modifiers, dice_class, rng=None)
       │         └─ RollModifier.roll(dice_class, rng=None)
       │              └─ dice_class.roll(expr, rng=rng)  ← recursive, propagates rng
       └─ Dice._parse_with_precedence(expr, modifiers, rng=None)
            └─ [same RollResultSet path as above]

DiceRoller.roll_standard_die(sides, rng=None)   ← _randint(rng, 1, sides)
DiceRoller.roll_fudge_die(rng=None)             ← _randint(rng, 1, 6)
DiceRoller.roll_percentile_die(rng=None)        ← _randint(rng, 0, 9) × 2
Dice._handle_goodflux_roll(rng=None)            ← passes rng to DiceRoller
Dice._handle_badflux_roll(rng=None)             ← passes rng to DiceRoller
```

**Rationale**: Explicit parameter threading is the only approach that is thread-safe by construction (no shared mutable state), testable without patching globals, and consistent with the existing `debug=` / `logger=` pattern in the same call chain.

**Alternatives considered**:
- Thread-local global (`threading.local()`): Safe across threads but requires setup/teardown around every call. Hidden state is harder to test and reason about. Rejected.
- Class-level setter `Dice.set_rng(rng)`: Not thread-safe. Multiple concurrent callers would stomp each other's rng. Rejected (confirmed in clarifications).
- Context manager: Cleaner than class-level setter (could use `threading.local` internally) but adds complexity for no benefit given the per-call approach is already clean. Rejected.

---

## Decision 4: CLI `--seed` Flag

**Decision**: Add `--seed N` integer flag to `tools/roll.py`. When provided, construct `random.Random(N)` and pass it as `rng=` to `Dice.roll()`. Include seed in `--json` output when used.

**Rationale**: Provides the primary use case for RNG injection at the CLI level — reproducible rolls for sharing, testing, or demos. Consistent with the CLI interface protocol in the constitution (`--debug`, `--json`, `--count` pattern).

**JSON output with seed**:
```json
{
  "result": 14,
  "description": "14 = 14 (1d20: 14)",
  "seed": 42
}
```

**Alternatives considered**:
- `--rng-class` for arbitrary RNG class injection: Overkill for a CLI tool. Callers needing custom RNGs use the Python API. Rejected.

---

## Decision 5: Debug Logging for RNG

**Decision**: When `rng` is not `None`, emit a single debug log line at `[START]`:  
`DEBUG: [RNG] Custom RNG in use: {type(rng).__name__}`

**Rationale**: Satisfies the constitution's observability requirement. Makes it immediately clear in debug output whether a seeded or stdlib RNG is active, aiding troubleshooting of non-random results.

---

## Summary Table

| Unknown | Decision | Rationale |
|---------|----------|-----------|
| RNG protocol contract | `random() -> float` duck type | Lowest friction; matches stdlib `random.Random` primitive |
| `randint` derivation | `int(rng.random() * n) + a` helper | Negligible bias for d4–d100; trivially simple |
| Propagation strategy | Explicit keyword arg through full chain | Thread-safe; testable; consistent with existing patterns |
| CLI exposure | `--seed N` integer flag | Primary use case; simple; JSON-includable |
| Debug observability | Log RNG type at `[START]` | Satisfies constitution observability principle |
