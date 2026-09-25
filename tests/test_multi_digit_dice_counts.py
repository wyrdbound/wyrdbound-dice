"""A dice count of two or more digits is one dice term (expression-validation §1a).

The lexer used to decide "dice or number" by peeking one character, so ``10d6``
lexed as the number ``10`` and an invalid ``d``. Every such expression with an
operator fell back to a method that summed dice and dropped everything else:
``10d6 - 10d6`` came to 80 and ``10d6 + 3`` to 40.
"""

import pytest

from wyrdbound_dice import Dice
from wyrdbound_dice.expression_lexer import ExpressionLexer
from wyrdbound_dice.expression_token import TokenType


class _Fours:
    """Every d6 shows 4: ``1 + int(0.5 * 6)``."""

    def random(self) -> float:
        return 0.5


@pytest.mark.parametrize(
    ("expr", "total"),
    [
        ("10d6 - 10d6", 0),
        ("10d6 + 3", 43),
        ("12d6 - 2", 46),
        ("100d6 + 1d6", 404),
        ("2d6 + 10d6", 48),
    ],
)
def test_multi_digit_count_arithmetic(expr: str, total: int) -> None:
    assert Dice.roll(expr, rng=_Fours()).total == total


def test_multi_digit_count_is_one_dice_token() -> None:
    lexer = ExpressionLexer("10d6")
    token = lexer.get_next_token()
    assert (token.type, token.value) == (TokenType.DICE, "10d6")
    assert lexer.get_next_token().type == TokenType.EOF
