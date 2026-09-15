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


def test_trace_sources_tag_rerolls():
    r = roll("8d6r1<=1").results[0]
    all_sources = [s for t in r.dice_traces for s in t["sources"]]
    assert "reroll" in all_sources
    assert set(all_sources) <= {"roll", "reroll", "explosion"}
    for trace in r.dice_traces:
        assert trace["sources"][0] == "roll"


def test_kept_indices_handles_ties():
    from wyrdbound_dice.roll_result import RollResult

    r = RollResult(4, "6", [3, 3, 5, 1], keep_operations=[("h", 2)])
    assert len(r.kept_indices) == 2
    assert len(r.dropped_indices) == 2
    assert 2 in r.kept_indices
    assert set(r.kept_indices) | set(r.dropped_indices) == {0, 1, 2, 3}
    assert len(set(r.kept_indices) & {0, 1}) == 1
