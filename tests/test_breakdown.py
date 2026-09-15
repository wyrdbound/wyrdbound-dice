"""Tests for the structured roll breakdown."""

import random

from wyrdbound_dice import Dice


def roll(expr, seed=42, **kw):
    """Roll an expression with a fixed seed."""
    return Dice.roll(expr, rng=random.Random(seed), **kw)


def test_dice_traces_present():
    result = roll("3d6")
    dice_traces = result.results[0].dice_traces
    assert isinstance(dice_traces, list)
    assert len(dice_traces) == 3
    for trace in dice_traces:
        assert set(trace) == {"faces", "sources", "value"}
