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


def test_traces_concatenate_to_all_rolls():
    for expr in ["3d6", "2d6r1<=2", "2d6e", "4dF", "1d%"]:
        r = roll(expr).results[0]
        faces = [f for t in r.dice_traces for f in t["faces"]]
        assert faces == r.all_rolls
