"""``validate`` checks an expression without rolling it (expression-validation §4).

It runs the pre-flight ``roll`` runs and nothing else, so it accepts exactly
what ``roll`` accepts, raises what ``roll`` would raise, and never draws
randomness.
"""

import random

import pytest
from format_corpus import EXPRESSIONS

import wyrdbound_dice
from wyrdbound_dice import (
    Dice,
    DivisionByZeroError,
    InfiniteConditionError,
    ParseError,
)

# The corpus records two expressions whose snapshot is an error; they are
# checked in INVALID instead.
CORPUS_ERRORS = {"1d6 / 0", "1d6r<=6"}

VALID = sorted(
    (set(EXPRESSIONS) - CORPUS_ERRORS)
    | {
        "1d8r<5",
        "4d6r<=2kh3",
        "1d6e",
        "1d10e>=9",
        "4dF",
        "FUDGE + BOON",
        "GOODFLUX",
        "BADFLUX",
        "2d%kh1",
        "4d6 dh 3",
        "10d6 - 10d6",
        "((2d6+1)*2)",
    }
)

INVALID = [
    ("2d6 banana", ParseError),
    ("1d20+{{ x }}", ParseError),
    ("2d6+3 # note", ParseError),
    ("3d6 5d8", ParseError),
    ("GOODFLUX + 3", ParseError),
    ("1d6r", ParseError),
    ("", ParseError),
    ("1d6 +", ParseError),
    ("1" + "0" * 6 + "d6", ParseError),
    ("1d6r<=6", InfiniteConditionError),
    ("1d6e>=1", InfiniteConditionError),
    ("1d6 / 0", DivisionByZeroError),
    ("2d6 / (3 - 3)", DivisionByZeroError),
]


@pytest.fixture
def no_randomness(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any draw from the random module fail the test."""

    def draw(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("validate drew randomness")

    for name in ("random", "randint", "randrange", "choice", "uniform"):
        monkeypatch.setattr(random, name, draw)
    monkeypatch.setattr(random.Random, "random", draw)


@pytest.mark.parametrize("expr", VALID)
def test_valid_expressions_validate(expr: str, no_randomness: None) -> None:
    assert Dice.validate(expr) is None
    assert wyrdbound_dice.validate(expr) is None


@pytest.mark.parametrize("expr", VALID)
def test_valid_expressions_also_roll(expr: str) -> None:
    Dice.roll(expr)


@pytest.mark.parametrize(("expr", "error"), INVALID)
def test_invalid_expressions_raise_what_roll_raises(
    expr: str, error: type, no_randomness: None
) -> None:
    with pytest.raises(error):
        Dice.validate(expr)


@pytest.mark.parametrize(("expr", "error"), INVALID)
def test_roll_agrees(expr: str, error: type) -> None:
    with pytest.raises(error):
        Dice.roll(expr)


def test_dice_dependent_division_is_a_rolling_error(no_randomness: None) -> None:
    # A divisor with no dice is known now; 1d2 - 1 is zero only on some rolls.
    assert Dice.validate("1d6 / (1d2 - 1)") is None
