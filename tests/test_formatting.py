"""Tests for the formatter, built against hand-constructed breakdowns."""

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
