# Public API Contract: wyrdbound-dice

**Feature**: addRNGInjection  
**Date**: 2026-05-03  
**Version**: 0.0.3 (planned)

---

## `Dice.roll()`

Primary entry point for all dice rolling.

```python
@classmethod
def roll(
    cls,
    expr: str,
    modifiers: Optional[Dict[str, Union[int, str]]] = None,
    debug: bool = False,
    logger=None,
    rng=None,
) -> RollResultSet:
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `expr` | `str` | required | Dice expression (e.g., `"2d6 + 3"`, `"4d6kh3"`, `"FUDGE"`) |
| `modifiers` | `dict` or `None` | `None` | Named modifiers: `{"Name": int_or_expr}` |
| `debug` | `bool` | `False` | Enable structured debug logging |
| `logger` | logger or `None` | `None` | Custom logger (Python logging or `StringLogger`) |
| `rng` | object or `None` | `None` | **New.** Any object with `random() -> float`. When `None`, stdlib random is used. |

### RNG Protocol

`rng` must satisfy:

```python
rng.random() -> float  # Returns value in [0.0, 1.0)
```

The same `rng` instance is used for **all** dice rolled in the call, including dice inside modifier expressions. Callers must not share a single `rng` instance across concurrent threads.

### Returns

`RollResultSet` with:
- `.total` — final integer result
- `.results` — list of `RollResult` per dice sub-expression  
- `.modifiers` — list of `RollModifier` with resolved values
- `str(result)` — human-readable description (e.g., `"14 = 9 (2d6: 5, 4) + 5"`)

### Raises

| Exception | Condition |
|-----------|-----------|
| `ParseError` | Invalid or malformed dice expression |
| `DivisionByZeroError` | Division by zero in expression |
| `InfiniteConditionError` | Reroll or explode condition matches all possible values |

### Examples

```python
from wyrdbound_dice import Dice
import random

# Existing usage — unchanged
result = Dice.roll("2d6 + 3")
result = Dice.roll("4d6kh3", debug=True)

# Seeded roll — reproducible
rng = random.Random(42)
result = Dice.roll("2d6 + 3", rng=rng)
assert result.total == Dice.roll("2d6 + 3", rng=random.Random(42)).total

# Seeded roll with dice modifiers — rng propagates to modifier dice
rng = random.Random(99)
result = Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=rng)

# Deterministic mock for unit testing
from unittest.mock import Mock
mock_rng = Mock()
mock_rng.random.return_value = 0.99  # Always max
result = Dice.roll("1d6", rng=mock_rng)
assert result.total == 6
```

---

## `roll()` convenience function

Top-level module function. Identical contract to `Dice.roll()`.

```python
def roll(
    expression: str,
    modifiers=None,
    debug: bool = False,
    debug_logger=None,
    rng=None,
) -> RollResultSet:
```

Note: parameter is named `debug_logger` (not `logger`) for historical reasons. Both `Dice.roll()` and `roll()` accept the same `rng` contract.

---

## CLI: `tools/roll.py`

### Updated Usage

```
python tools/roll.py <expression> [options]
```

### Options

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Detailed breakdown |
| `-n N, --count N` | Roll N times |
| `--json` | JSON output |
| `--debug` | Structured debug log |
| `--seed N` | **New.** Integer seed for reproducible rolls. Uses `random.Random(N)` as `rng`. |

### `--seed` behaviour

- Without `--seed`: Uses stdlib random (non-deterministic)
- With `--seed N`: Same seed always produces the same result(s)
- With `--seed` + `--json`: Seed value included in output

### JSON output with `--seed`

Single roll:
```json
{
  "result": 14,
  "description": "14 = 14 (1d20: 14)",
  "seed": 42
}
```

Multiple rolls (`--count N`):
```json
{
  "seed": 42,
  "results": [
    {"result": 4, "description": "4 = 4 (1d6: 4)"},
    {"result": 6, "description": "6 = 6 (1d6: 6)"}
  ]
}
```

---

## Backward Compatibility

All changes are **additive**. No existing parameter names, return types, or exception types change.

| Caller pattern | Status |
|----------------|--------|
| `Dice.roll("2d6")` | ✅ Unchanged |
| `Dice.roll("2d6", {"Str": 3})` | ✅ Unchanged |
| `Dice.roll("2d6", debug=True, logger=my_logger)` | ✅ Unchanged |
| `from wyrdbound_dice import roll; roll("1d20")` | ✅ Unchanged |
| `python tools/roll.py "1d20"` | ✅ Unchanged |
