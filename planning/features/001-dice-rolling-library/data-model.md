# Data Model: Dice Rolling Library

**Feature**: addRNGInjection  
**Date**: 2026-05-03

---

## Entity Overview

```text
Dice
 └── roll(expr, modifiers, debug, logger, rng) ──► RollResultSet
                                                        ├── results: List[RollResult]
                                                        └── modifiers: List[RollModifier]
                                                               └── dice_result: RollResultSet (recursive)

RNG Protocol (duck type)
 └── random() -> float [0.0, 1.0)

DiceRoller (internal)
 └── _randint(rng, a, b) -> int
```

---

## Entities

### `Dice`

Main entry point. Stateless (all methods are `@classmethod` or `@staticmethod`).

| Method | Signature | Notes |
|--------|-----------|-------|
| `roll` | `(expr: str, modifiers=None, debug=False, logger=None, rng=None) -> RollResultSet` | **`rng` is new** |
| `roll_with_precedence` | `(expr: str, modifiers=None, rng=None) -> RollResultSet` | **`rng` is new** |

---

### `RollResultSet`

Holds the full result of a `Dice.roll()` call.

| Field | Type | Description |
|-------|------|-------------|
| `results` | `List[RollResult]` | One entry per dice sub-expression |
| `modifiers` | `List[RollModifier]` | Applied named modifiers |
| `_override_total` | `Optional[int]` | Set for GOODFLUX/BADFLUX special cases |
| `_override_description` | `Optional[str]` | Set for GOODFLUX/BADFLUX special cases |

| Property | Type | Description |
|----------|------|-------------|
| `subtotal` | `int` | Sum of all dice results before modifiers |
| `total` | `int` | Final result including modifiers |

**Constructor change**: `__init__(results, modifiers=None, dice_class=None, rng=None)`  
The `rng` is passed to each `RollModifier.roll(dice_class, rng=rng)` call.

---

### `RollModifier`

Represents one named modifier entry — either a static integer or a dice expression.

| Field | Type | Description |
|-------|------|-------------|
| `raw_value` | `Union[int, str]` | Original value as provided by caller |
| `description` | `str` | Modifier name (e.g., `"Strength"`, `"Bless"`) |
| `sign` | `str` | `"+"` or `"-"` |
| `value` | `int` | Resolved integer value after rolling |
| `is_dice` | `bool` | `True` if modifier is a dice expression |
| `dice_expression` | `str` | Dice expression string (e.g., `"1d4"`) |
| `dice_result` | `Optional[RollResultSet]` | Result of rolling the dice modifier |

**Method change**: `roll(dice_class, rng=None)`  
When `is_dice` is `True`, calls `dice_class.roll(self.dice_expression, rng=rng)` — propagating `rng` into the nested roll.

---

### `RollResult`

Represents a single parsed dice group (e.g., `2d6kh1`). **Unchanged by this feature.**

| Field | Type | Description |
|-------|------|-------------|
| `num` | `int` | Number of dice rolled |
| `sides` | `Union[int, str]` | Sides per die (`int`, `"F"`, `"%"`) |
| `rolls` | `List[int]` | All individual die rolls (pre-keep/drop) |
| `kept` | `List[int]` | Dice kept after keep/drop operations |
| `all_rolls` | `List[int]` | All rolls including rerolls and explosions |
| `multiply` | `int` | Multiplier (default 1) |
| `divide` | `int` | Divisor (default 1) |

---

### `DiceRoller` (internal)

Static methods for rolling individual dice. All three rolling methods gain `rng=None`.

| Method | Signature change | Effect |
|--------|-----------------|--------|
| `roll_standard_die` | `(sides: int, rng=None) -> int` | Uses `_randint(rng, 1, sides)` |
| `roll_fudge_die` | `(rng=None) -> Tuple[int, int]` | Uses `_randint(rng, 1, 6)` |
| `roll_percentile_die` | `(rng=None) -> Tuple[int, int, int]` | Uses `_randint(rng, 0, 9)` × 2 |

---

### `_randint` (module-private helper, new)

```
_randint(rng, a: int, b: int) -> int
```

| Input | When `rng is None` | When `rng` provided |
|-------|--------------------|---------------------|
| Returns | `random.randint(a, b)` | `int(rng.random() * (b - a + 1)) + a` |

Defined at module level in `dice.py`. Not exported.

---

### RNG Protocol (duck type, new)

Not a class — a behavioural contract satisfied by any object implementing:

```
random() -> float   # Returns value in [0.0, 1.0)
```

**Compatible out of the box**:

| Object | Notes |
|--------|-------|
| `random.Random()` | Stdlib; supports seeding via `random.Random(seed)` |
| `random.Random(seed)` | Seeded for reproducibility |
| Any `Mock` with `random` attribute | e.g., `unittest.mock.Mock(random=lambda: 0.5)` |

**Not directly compatible** (requires thin wrapper):

| Object | Reason |
|--------|--------|
| `numpy.random.Generator` | Exposes `random()` — actually compatible directly |
| Bare `lambda: 0.5` | Works as `rng` if assigned to an object with `.random` attribute |

---

### State Transitions

RNG state is entirely owned by the caller-supplied object. `Dice.roll()` is stateless with respect to RNG — it reads from `rng.random()` and never writes to or retains a reference to `rng` after the call returns.

```
Before call:  rng.state = S0
During call:  rng.state = S1...Sn  (advances once per die rolled)
After call:   rng.state = Sn        (caller retains full control)
```

This means the caller can replay a full session by resetting their `rng` to `S0` (e.g., `random.Random(seed)`).
