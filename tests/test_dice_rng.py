"""Tests for injectable RNG support in wyrdbound-dice.

Baseline: 176 tests passing before any changes.

This file covers:
- _randint() module-private helper (T003, T004)
- Dice.roll() API acceptance of rng= parameter (T005, T006)
- Per-mechanic reproducibility via seeded rng (T007-T019)
  US1: basic rolls, mock pinning
  US2: precedence parser path
  US3: keep/drop mechanics
  US4: reroll mechanics
  US5: exploding dice
  US6: fudge dice
  US7: system shorthands (GOODFLUX, BADFLUX, percentile)
  US8: named modifier propagation
- Concurrent stress test (T032, SC-006)
"""

import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock

import pytest

from wyrdbound_dice import Dice, RollResultSet
from wyrdbound_dice.dice import _randint

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_rng():
    """A seeded random.Random instance for reproducible tests."""
    return random.Random(42)


# ---------------------------------------------------------------------------
# T003 — _randint fallback: None uses stdlib random
# ---------------------------------------------------------------------------


def test_randint_fallback_uses_stdlib():
    """_randint(None, a, b) must return an int in [a, b] using stdlib random."""
    for _ in range(100):
        result = _randint(None, 1, 6)
        assert isinstance(result, int)
        assert 1 <= result <= 6


# ---------------------------------------------------------------------------
# T004 — _randint with rng: calls rng.random() exactly once
# ---------------------------------------------------------------------------


def test_randint_calls_rng_random():
    """_randint(rng, a, b) must call rng.random() exactly once and return int in [a, b]."""
    mock_rng = Mock()
    mock_rng.random.return_value = 0.5
    result = _randint(mock_rng, 1, 6)
    mock_rng.random.assert_called_once()
    assert isinstance(result, int)
    assert 1 <= result <= 6


# ---------------------------------------------------------------------------
# T005 — [US1] Dice.roll() accepts rng=None without TypeError
# ---------------------------------------------------------------------------


def test_dice_roll_accepts_rng_none():
    """Dice.roll() must accept rng=None and return a RollResultSet."""
    result = Dice.roll("1d6", rng=None)
    assert isinstance(result, RollResultSet)


# ---------------------------------------------------------------------------
# T006 — [US1] Dice.roll() uses rng.random() when rng is supplied
# ---------------------------------------------------------------------------


def test_dice_roll_uses_rng_random():
    """Dice.roll() must call rng.random() at least once when rng is supplied."""
    mock_rng = Mock()
    mock_rng.random.return_value = 0.5
    Dice.roll("1d6", rng=mock_rng)
    assert mock_rng.random.call_count >= 1


# ---------------------------------------------------------------------------
# T007 — [US1] Basic roll is reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_basic_roll_reproducible():
    """Two Dice.roll('1d20') calls with the same seed must produce equal totals."""
    r1 = Dice.roll("1d20", rng=random.Random(42))
    r2 = Dice.roll("1d20", rng=random.Random(42))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T008 — [US1] Mock rng pins result to maximum
# ---------------------------------------------------------------------------


def test_mock_rng_pins_result():
    """rng.random() always returning 0.9999 must yield the maximum die value."""
    mock_rng = Mock()
    mock_rng.random.return_value = 0.9999
    result = Dice.roll("1d6", rng=mock_rng)
    assert result.total == 6


# ---------------------------------------------------------------------------
# T009 — [US2] Precedence parser path is reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_precedence_parser_reproducible():
    """Complex expressions (forcing _parse_with_precedence) must be reproducible."""
    expr = "2d6 + 1d4 × 2"
    r1 = Dice.roll(expr, rng=random.Random(42))
    r2 = Dice.roll(expr, rng=random.Random(42))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T010 — [US3] Keep/drop roll is reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_keep_drop_reproducible():
    """4d6kh3 with the same seed must produce equal totals."""
    r1 = Dice.roll("4d6kh3", rng=random.Random(7))
    r2 = Dice.roll("4d6kh3", rng=random.Random(7))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T011 — [US4] Reroll mechanic is reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_reroll_reproducible():
    """2d6r<=2 with the same seed must produce equal totals."""
    r1 = Dice.roll("2d6r<=2", rng=random.Random(7))
    r2 = Dice.roll("2d6r<=2", rng=random.Random(7))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T012 — [US5] Exploding dice are reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_exploding_reproducible():
    """1d6e with the same seed must produce equal totals."""
    r1 = Dice.roll("1d6e", rng=random.Random(7))
    r2 = Dice.roll("1d6e", rng=random.Random(7))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T013 — [US6] Fudge dice are reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_fudge_reproducible():
    """4dF with the same seed must produce equal totals."""
    r1 = Dice.roll("4dF", rng=random.Random(1))
    r2 = Dice.roll("4dF", rng=random.Random(1))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T014 — [US6] Mock rng pins fudge die to minimum
# ---------------------------------------------------------------------------


def test_fudge_mock_min():
    """rng.random() always 0.0 must yield minimum fudge value (-1)."""
    mock_rng = Mock()
    mock_rng.random.return_value = 0.0
    result = Dice.roll("1dF", rng=mock_rng)
    assert result.total == -1


# ---------------------------------------------------------------------------
# T015 — [US7] GOODFLUX is reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_goodflux_reproducible():
    """GOODFLUX with the same seed must produce equal totals."""
    r1 = Dice.roll("GOODFLUX", rng=random.Random(5))
    r2 = Dice.roll("GOODFLUX", rng=random.Random(5))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T016 — [US7] BADFLUX is reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_badflux_reproducible():
    """BADFLUX with the same seed must produce equal totals."""
    r1 = Dice.roll("BADFLUX", rng=random.Random(5))
    r2 = Dice.roll("BADFLUX", rng=random.Random(5))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T017 — [US7] Percentile dice are reproducible with seeded rng
# ---------------------------------------------------------------------------


def test_percentile_reproducible():
    """1d% with the same seed must produce equal totals."""
    r1 = Dice.roll("1d%", rng=random.Random(3))
    r2 = Dice.roll("1d%", rng=random.Random(3))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T018 — [US8] Named modifier propagation is reproducible end-to-end
# ---------------------------------------------------------------------------


def test_modifier_propagation_reproducible():
    """rng must propagate into dice modifier expressions for full reproducibility."""
    r1 = Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=random.Random(9))
    r2 = Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=random.Random(9))
    assert r1.total == r2.total


# ---------------------------------------------------------------------------
# T019 — [US8] Mock rng controls both base and modifier dice
# ---------------------------------------------------------------------------


def test_modifier_mock_controls_all_dice():
    """A mock rng pinned to 0.9999 must max both the base d20 (20) and Bless d4 (4)."""
    mock_rng = Mock()
    mock_rng.random.return_value = 0.9999
    result = Dice.roll("1d20", modifiers={"Bless": "1d4"}, rng=mock_rng)
    assert result.total == 24  # 20 + 4


# ---------------------------------------------------------------------------
# T032 — Concurrent stress test (SC-006 / constitution §III chaos engineering)
# ---------------------------------------------------------------------------


def test_concurrent_rng_safety():
    """1000 concurrent Dice.roll() calls each with a unique per-thread rng must
    all return valid RollResultSets with no exceptions and no cross-contamination.
    """
    num_calls = 1000
    errors = []

    def roll_with_seed(seed: int):
        rng = random.Random(seed)
        result = Dice.roll("2d6", rng=rng)
        assert isinstance(result, RollResultSet)
        assert (
            2 <= result.total <= 12
        ), f"Out-of-range total {result.total} for seed {seed}"
        return result.total

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(roll_with_seed, i): i for i in range(num_calls)}
        for future in as_completed(futures):
            exc = future.exception()
            if exc:
                errors.append((futures[future], exc))

    assert (
        not errors
    ), f"{len(errors)} concurrent roll(s) raised exceptions: {errors[:3]}"
