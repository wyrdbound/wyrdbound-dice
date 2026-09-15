# Quickstart: RNG Injection

**Feature**: addRNGInjection  
**Date**: 2026-05-03

---

## What Is RNG Injection?

By default, `Dice.roll()` uses Python's stdlib random module — results are non-deterministic. RNG injection lets you supply your own random number source, making any roll reproducible. The only requirement is that your object has a `random()` method returning a float in `[0.0, 1.0)`.

---

## Basic Usage: Seeded Rolls

```python
import random
from wyrdbound_dice import Dice

# Create a seeded RNG
rng = random.Random(42)

# This will always produce the same result for seed 42
result = Dice.roll("2d6 + 3", rng=rng)
print(result)  # e.g., "11 = 8 (2d6: 5, 3) + 3"

# Replaying: same seed → same result
result2 = Dice.roll("2d6 + 3", rng=random.Random(42))
assert result.total == result2.total  # Always true
```

---

## Testing: Deterministic Dice in Unit Tests

```python
from unittest.mock import Mock
from wyrdbound_dice import Dice

# Pin every die to its maximum value
max_rng = Mock()
max_rng.random.return_value = 0.9999

result = Dice.roll("1d6", rng=max_rng)
assert result.total == 6

# Pin every die to its minimum value
min_rng = Mock()
min_rng.random.return_value = 0.0

result = Dice.roll("1d6", rng=min_rng)
assert result.total == 1

# Sequence of values for complex expressions
values = iter([0.9, 0.1, 0.5])  # Controls each die in order
seq_rng = Mock()
seq_rng.random.side_effect = lambda: next(values)

result = Dice.roll("3d6", rng=seq_rng)
# Dice rolled: 6, 1, 3  →  total = 10
assert result.total == 10
```

---

## Modifier Propagation

When modifiers contain dice expressions, the same `rng` is used for those rolls too:

```python
import random
from wyrdbound_dice import Dice

rng = random.Random(7)

# "Bless" is a 1d4 dice modifier — rolled using the same rng
result = Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=rng)
print(result)  # e.g., "17 = 14 (1d20: 14) + 3 (Bless: 3)"

# Replay identically
result2 = Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=random.Random(7))
assert result.total == result2.total
```

---

## Simulations

Seeded RNG is ideal for Monte Carlo simulations where you want reproducible runs:

```python
import random
from wyrdbound_dice import Dice

def simulate_ability_scores(seed: int) -> list[int]:
    """Generate a full D&D 5e ability score array reproducibly."""
    rng = random.Random(seed)
    return [Dice.roll("4d6kh3", rng=rng).total for _ in range(6)]

# Always the same scores for seed 42
scores = simulate_ability_scores(42)
print(scores)  # e.g., [14, 11, 13, 16, 10, 15]
assert scores == simulate_ability_scores(42)
```

---

## CLI: Reproducible Rolls with `--seed`

```bash
# Same seed always gives the same result
python tools/roll.py "2d6 + 3" --seed 42
# 11 = 8 (2d6: 5, 3) + 3

python tools/roll.py "2d6 + 3" --seed 42
# 11 = 8 (2d6: 5, 3) + 3

# JSON output includes seed
python tools/roll.py "1d20" --seed 42 --json
# {"result": 14, "description": "14 = 14 (1d20: 14)", "seed": 42}

# Combine with --count for reproducible batches
python tools/roll.py "4d6kh3" --seed 42 --count 6
```

---

## Custom RNG Objects

Any object with a `random()` method works:

```python
class AlwaysMaxRNG:
    """A deterministic RNG that always returns maximum values. For testing."""
    def random(self) -> float:
        return 0.9999

result = Dice.roll("1d20", rng=AlwaysMaxRNG())
assert result.total == 20
```

---

## Thread Safety

Each call to `Dice.roll()` uses only the `rng` instance you pass in — there is no shared global RNG state. However, **do not share a single `rng` instance across threads** without external synchronization, as `random.Random` is not thread-safe.

```python
import threading
import random
from wyrdbound_dice import Dice

def roll_in_thread(seed: int):
    # Each thread gets its own RNG — safe
    rng = random.Random(seed)
    result = Dice.roll("2d6", rng=rng)
    print(result.total)

threads = [threading.Thread(target=roll_in_thread, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```
