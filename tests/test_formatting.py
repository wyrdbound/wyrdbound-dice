"""Tests for the formatter, built against hand-constructed breakdowns."""

import dataclasses

import pytest

from wyrdbound_dice.breakdown import DiceGroup, Die


def test_enums_exist():
    from wyrdbound_dice.formatting import Dropped, Percentile

    assert Dropped.SHOWN
    assert Dropped.HIDDEN
    assert Dropped.MARKED
    assert len(list(Dropped)) == 3
    assert Percentile.PAIR
    assert Percentile.VALUE
    assert len(list(Percentile)) == 2


def test_rollformat_defaults():
    from wyrdbound_dice.formatting import Dropped, Percentile, RollFormat

    fmt = RollFormat()
    assert fmt.layout == "{total} = {breakdown}"
    assert fmt.show_notation is True
    assert fmt.dropped == Dropped.SHOWN
    assert fmt.show_rerolls is True
    assert fmt.modifier_depth == 2
    assert fmt.die_separator == ", "
    assert fmt.group_open == "("
    assert fmt.group_close == ")"
    assert fmt.notation_separator == ": "
    assert fmt.multiply_symbol == "x"
    assert fmt.divide_symbol == "/"
    assert fmt.dropped_marker == "~{value}~"
    assert fmt.fudge_symbols == ("-", "B", "+")
    assert fmt.percentile == Percentile.PAIR
    hash(fmt)
    with pytest.raises(dataclasses.FrozenInstanceError):
        fmt.modifier_depth = 0


def test_layout_validation():
    from wyrdbound_dice.formatting import RollFormat

    with pytest.raises(ValueError):
        RollFormat(layout="no placeholders")
    with pytest.raises(ValueError) as excinfo:
        RollFormat(layout="{total} {bogus}")
    message = str(excinfo.value)
    assert "total" in message
    assert "breakdown" in message
    assert "expression" in message
    with pytest.raises(ValueError):
        RollFormat(layout="{}")
    assert RollFormat(layout="{total}")
    assert RollFormat(layout="{expression}")


def test_format_group_standard():
    from wyrdbound_dice.formatting import DefaultFormatter

    assert DefaultFormatter().format_group(simple_group()) == "8 (2d6: 6, 2)"


def simple_group():
    """A plain 2d6 group: dice 6 and 2, both kept, subtotal 8."""
    return DiceGroup(
        num=2,
        sides="6",
        kind="standard",
        notation="2d6",
        dice=(
            Die(value=6, faces=(6,), sources=("roll",), kept=True),
            Die(value=2, faces=(2,), sources=("roll",), kept=True),
        ),
        subtotal=8,
        total=8,
    )


def keep_group():
    """A 4d6kh3 group: the 1 is dropped, dice 2, 5, 6 kept."""
    return DiceGroup(
        num=4,
        sides="6",
        kind="standard",
        notation="4d6kh3",
        dice=(
            Die(value=1, faces=(1,), sources=("roll",), kept=False),
            Die(value=2, faces=(2,), sources=("roll",), kept=True),
            Die(value=5, faces=(5,), sources=("roll",), kept=True),
            Die(value=6, faces=(6,), sources=("roll",), kept=True),
        ),
        keep_operations=(("h", 3),),
        subtotal=13,
        total=13,
    )


def fudge_group():
    """A fudge group with raw faces 1, 3, 5."""
    return DiceGroup(
        num=3,
        sides="F",
        kind="fudge",
        notation="3dF",
        dice=(
            Die(value=-1, faces=(1,), sources=("roll",), kept=True),
            Die(value=0, faces=(3,), sources=("roll",), kept=True),
            Die(value=1, faces=(5,), sources=("roll",), kept=True),
        ),
        subtotal=0,
        total=0,
    )
