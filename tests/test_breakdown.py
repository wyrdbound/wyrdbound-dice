"""Tests for the structured roll breakdown."""

import dataclasses
import random

import pytest

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


def test_breakdown_types_exist_and_are_frozen():
    from wyrdbound_dice.breakdown import (
        BinaryOp,
        DiceGroup,
        DiceNode,
        Die,
        Literal,
        ModifierBreakdown,
        RollBreakdown,
        UnaryOp,
    )

    die = Die(value=3, faces=(3,), sources=("roll",), kept=True)
    group = DiceGroup(num=1, sides="6")
    literal = Literal(value=1)
    dice_node = DiceNode(group=group)
    unary = UnaryOp(op="-", operand=literal, value=-1)
    binary = BinaryOp(left=literal, op="+", right=literal, value=2)
    modifier = ModifierBreakdown(name="Strength", value=3)
    breakdown = RollBreakdown(root=binary, total=2, expression="1 + 1", modifiers=())

    for obj in [
        die,
        group,
        literal,
        dice_node,
        unary,
        binary,
        modifier,
        breakdown,
    ]:
        assert dataclasses.is_dataclass(obj)
        with pytest.raises(dataclasses.FrozenInstanceError):
            obj.value = 0


def test_roll_result_breakdown_shape():
    from wyrdbound_dice.breakdown import DiceGroup

    result = roll("4d6kh3")
    g = result.results[0].breakdown
    assert isinstance(g, DiceGroup)
    assert g.num == 4
    assert g.sides == "6"
    assert g.kind == "standard"
    assert len(g.dice) == 4
    assert sum(1 for d in g.dice if not d.kept) == 1
    assert g.keep_operations == (("h", 3),)
    assert g.subtotal == sum(d.value for d in g.dice if d.kept)


def test_breakdown_kinds():
    assert roll("4dF").results[0].breakdown.kind == "fudge"
    assert roll("1d%").results[0].breakdown.kind == "percentile"
    assert roll("2d6").results[0].breakdown.kind == "standard"
