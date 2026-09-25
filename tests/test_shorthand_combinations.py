"""Shorthands expand wherever they appear, and nothing else changes case.

expression-validation §1d: each shorthand used to be expanded into a fresh copy
of the *uppercased original*, so with two different shorthands only the last
survived — ``FUDGE + BOON`` rolled just ``3d6kh2`` — and any shorthand
uppercased the rest of the expression.
"""

import pytest

from wyrdbound_dice import Dice, ParseError
from wyrdbound_dice.dice import ExpressionProcessor


class _High:
    """Every die shows its top face: d6 is 6, a Fudge die is +1."""

    def random(self) -> float:
        return 0.99


@pytest.mark.parametrize(
    ("expr", "expanded"),
    [
        ("FUDGE + BOON", "4dF + 3d6kh2"),
        ("boon - bane", "3d6kh2 - 3d6kl2"),
        ("FUDGE + 1d6", "4dF + 1d6"),
        ("PERCENTILE", "1d%"),
        ("perc + 1", "1d% + 1"),
        ("FLUX + 1", "1d6 - 1d6 + 1"),
    ],
)
def test_every_shorthand_expands(expr: str, expanded: str) -> None:
    assert ExpressionProcessor.process_shorthands(expr) == expanded


def test_two_shorthands_both_roll() -> None:
    # 4dF of +1s is 4; 3d6kh2 of sixes is 12. Dropping FUDGE would give 12.
    assert Dice.roll("4dF", rng=_High()).total == 4
    assert Dice.roll("FUDGE + BOON", rng=_High()).total == 16


@pytest.mark.parametrize("expr", ["GOODFLUX", "goodflux", " BADFLUX "])
def test_flux_alone_is_special(expr: str) -> None:
    assert ExpressionProcessor.process_shorthands(expr) in (
        "GOODFLUX_SPECIAL",
        "BADFLUX_SPECIAL",
    )


def test_flux_inside_a_word_is_not_a_shorthand() -> None:
    with pytest.raises(ParseError):
        Dice.roll("GOODFLUXY")
