"""Text the grammar does not describe is an error, never ignored.

expression-validation §1b and §1c: a precedence-parser ``ParseError`` used to
fall back to a method that rolls every dice term it can find and ignores the
rest, so an unrendered template rolled a plain d20. Flux shorthands matched
anywhere in the expression and swallowed the rest of it.
"""

import pytest

from wyrdbound_dice import Dice, ParseError


@pytest.mark.parametrize(
    "expr",
    [
        "2d6 banana",
        "1d20+{{ x }}",
        "2d6+3 # note",
        "1d6 + 1d6 + zz",
        "3d6 5d8",
        "GOODFLUX + 3",
        "GOODFLUX banana",
        "BADFLUX - 1",
    ],
)
def test_unparsed_text_raises(expr: str) -> None:
    with pytest.raises(ParseError):
        Dice.roll(expr)


@pytest.mark.parametrize("expr", ["GOODFLUX", "BADFLUX", "goodflux", "3d6 + 5d8"])
def test_complete_expressions_still_roll(expr: str) -> None:
    assert Dice.roll(expr).total is not None
