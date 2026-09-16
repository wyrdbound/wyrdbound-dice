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


def test_layout_arrangements():
    from wyrdbound_dice.breakdown import BinaryOp, DiceNode, Literal, RollBreakdown
    from wyrdbound_dice.formatting import DefaultFormatter, RollFormat

    breakdown = RollBreakdown(
        root=BinaryOp(DiceNode(simple_group()), "+", Literal(3), 11),
        total=11,
        expression="2d6 + 3",
    )

    cases = [
        ("{total} = {breakdown}", "11 = 8 (2d6: 6, 2) + 3"),
        ("{breakdown}", "8 (2d6: 6, 2) + 3"),
        ("{total}", "11"),
        ("{breakdown} => {total}", "8 (2d6: 6, 2) + 3 => 11"),
        ("{expression}: {total}", "2d6 + 3: 11"),
        ("[{total}] {breakdown}", "[11] 8 (2d6: 6, 2) + 3"),
    ]
    for layout, expected in cases:
        assert DefaultFormatter(RollFormat(layout=layout)).format(breakdown) == expected


@pytest.mark.xfail(
    reason="Dropped.MARKED rendering lands in T075; T075 removes this marker",
    strict=True,
)
def test_layout_does_not_reparse_rendered_braces():
    from wyrdbound_dice.breakdown import DiceNode, RollBreakdown
    from wyrdbound_dice.formatting import DefaultFormatter, Dropped, RollFormat

    breakdown = RollBreakdown(
        root=DiceNode(keep_group()),
        total=13,
        expression="4d6kh3",
    )
    fmt = RollFormat(dropped=Dropped.MARKED, dropped_marker="{{{value}}}")
    output = DefaultFormatter(fmt).format(breakdown)
    assert "{1}" in output
    assert "~" not in output


def test_precedence_parenthesisation():
    from wyrdbound_dice.breakdown import BinaryOp, Literal
    from wyrdbound_dice.formatting import DefaultFormatter

    formatter = DefaultFormatter()
    cases = [
        (
            BinaryOp(BinaryOp(Literal(2), "+", Literal(3), 5), "x", Literal(2), 10),
            "(2 + 3) x 2",
        ),
        (
            BinaryOp(Literal(10), "-", BinaryOp(Literal(2), "x", Literal(3), 6), 4),
            "10 - 2 x 3",
        ),
        (
            BinaryOp(Literal(10), "-", BinaryOp(Literal(2), "-", Literal(3), -1), 11),
            "10 - (2 - 3)",
        ),
    ]
    for node, expected in cases:
        assert formatter.format_node(node) == expected


def test_glyph_overrides():
    from wyrdbound_dice.breakdown import BinaryOp, DiceNode, Literal, RollBreakdown
    from wyrdbound_dice.formatting import DefaultFormatter, RollFormat

    breakdown = RollBreakdown(
        root=BinaryOp(DiceNode(simple_group()), "+", Literal(3), 11),
        total=11,
        expression="2d6 + 3",
    )

    multiply = RollBreakdown(
        root=BinaryOp(DiceNode(simple_group()), "x", Literal(3), 24),
        total=24,
        expression="2d6 x 3",
    )
    out = DefaultFormatter(RollFormat(multiply_symbol="×")).format(multiply)
    assert "×" in out
    assert "x" not in out

    fmt = DefaultFormatter(RollFormat(die_separator=" "))
    assert fmt.format_group(simple_group()) == "8 (2d6: 6 2)"

    fmt = DefaultFormatter(RollFormat(group_open="[", group_close="]"))
    assert fmt.format_group(simple_group()) == "8 [2d6: 6, 2]"

    fmt = DefaultFormatter(RollFormat(show_notation=False))
    assert fmt.format_group(simple_group()) == "8 (6, 2)"
    assert DefaultFormatter(RollFormat()).format(breakdown) is not None


def test_fudge_symbols():
    from wyrdbound_dice.formatting import DefaultFormatter, RollFormat

    default = DefaultFormatter().format_group(fudge_group())
    assert "-, B, +" in default

    custom = DefaultFormatter(RollFormat(fudge_symbols=("-", "0", "+")))
    assert "-, 0, +" in custom.format_group(fudge_group())


def test_percentile_styles():
    from wyrdbound_dice.breakdown import DiceGroup, Die
    from wyrdbound_dice.formatting import DefaultFormatter, Percentile, RollFormat

    group = DiceGroup(
        num=1,
        sides="%",
        kind="percentile",
        notation="1d%",
        dice=(Die(value=60, faces=((60, 0),), sources=("roll",), kept=True),),
        subtotal=60,
        total=60,
    )
    pair = DefaultFormatter(RollFormat(percentile=Percentile.PAIR))
    assert "[60, 0]" in pair.format_group(group)

    value = DefaultFormatter(RollFormat(percentile=Percentile.VALUE))
    assert "60" in value.format_group(group)
    assert "[" not in value.format_group(group)


def test_zero_dice_group():
    from wyrdbound_dice.breakdown import DiceGroup
    from wyrdbound_dice.formatting import DefaultFormatter

    group = DiceGroup(num=0, sides="6", kind="standard", notation="0d6")
    assert DefaultFormatter().format_group(group) == "0 (0d6)"


def test_formatter_protocol_and_subclass():
    from wyrdbound_dice.breakdown import DiceNode, RollBreakdown
    from wyrdbound_dice.formatting import DefaultFormatter, Formatter

    class HashFormatter(DefaultFormatter):
        def format_die(self, die, group):
            return "#"

    breakdown = RollBreakdown(root=DiceNode(simple_group()), total=8, expression="2d6")
    assert HashFormatter().format(breakdown) == "8 = 8 (2d6: #, #)"

    class Duck:
        def format(self, breakdown):
            return "duck"

    assert isinstance(Duck(), Formatter)


def test_presets_exist():
    from wyrdbound_dice.formatting import RollFormat

    for preset in [
        RollFormat.STANDARD,
        RollFormat.COMPACT,
        RollFormat.MINIMAL,
        RollFormat.VERBOSE,
    ]:
        assert isinstance(preset, RollFormat)


def test_standard_equals_default():
    from wyrdbound_dice.formatting import RollFormat

    assert RollFormat.STANDARD == RollFormat()


def test_presets_render():
    import random

    from wyrdbound_dice import Dice
    from wyrdbound_dice.formatting import RollFormat

    result = Dice.roll("4d6kh3", rng=random.Random(42))
    assert str(result) == "8 = 8 (4d6kh3: 4, 1, 2, 2)"
    assert result.format(RollFormat.STANDARD) == str(result)
    assert result.format(RollFormat.MINIMAL) == "8"


@pytest.mark.xfail(
    reason="Dropped.MARKED rendering lands in T075; T075 removes this marker",
    strict=True,
)
def test_verbose_preset_marks_dropped_dice():
    import random

    from wyrdbound_dice import Dice
    from wyrdbound_dice.formatting import RollFormat

    result = Dice.roll("4d6kh3", rng=random.Random(42))
    assert result.format(RollFormat.VERBOSE) != str(result)


@pytest.fixture
def clean_default_format():
    yield
    from wyrdbound_dice.formatting import set_default_format

    set_default_format(None)


def test_module_default(clean_default_format):
    import random

    from wyrdbound_dice import Dice
    from wyrdbound_dice.formatting import (
        RollFormat,
        get_default_format,
        set_default_format,
    )

    assert get_default_format() == RollFormat.STANDARD

    result = Dice.roll("4d6kh3", rng=random.Random(42))
    set_default_format(RollFormat.COMPACT)
    assert result.format() == result.format(RollFormat.COMPACT)
    assert str(result) == "8 = 8 (4d6kh3: 4, 1, 2, 2)"

    set_default_format(None)
    assert get_default_format() == RollFormat.STANDARD


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
