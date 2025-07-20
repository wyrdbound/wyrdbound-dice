"""
WyrdBound Dice - A comprehensive dice rolling library for tabletop RPGs

This package provides powerful dice rolling capabilities with support for:
- Standard polyhedral dice (d4, d6, d8, d10, d12, d20, d100)
- Fudge dice for Fate Core/Accelerated systems
- Keep/drop mechanics (advantage/disadvantage, ability score generation)
- Exploding dice for Savage Worlds and other systems
- Reroll mechanics with various conditions
- Complex mathematical expressions with proper precedence
- Named system shorthands (FUDGE, BOON, BANE, FLUX, etc.)
- Unicode support for international characters
- Thread-safe operation for concurrent use

Main entry point is the Dice class with its static roll() method.

Example usage:
    >>> from wyrdbound_dice import Dice
    >>> result = Dice.roll("2d6 + 3")
    >>> print(f"Total: {result.total}, Description: {result.description}")

    >>> # Advantage roll
    >>> result = Dice.roll("2d20kh1")

    >>> # Exploding dice
    >>> result = Dice.roll("1d6e")

    >>> # Complex expression
    >>> result = Dice.roll("2d6 + 1d4 x 2 - 1")
"""

from .dice import Dice, RollModifier, RollResultSet
from .errors import DivisionByZeroError, InfiniteConditionError, ParseError
from .expression_token import TokenType
from .roll_result import RollResult
from .debug_logger import StringLogger, DebugLogger

__version__ = "1.0.0"
__author__ = "TheWyrdOne"
__email__ = "wyrdbound@proton.me"
__description__ = "A comprehensive dice rolling library for tabletop RPGs"

__all__ = [
    "Dice",
    "RollResult",
    "RollResultSet",
    "RollModifier",
    "ParseError",
    "DivisionByZeroError",
    "InfiniteConditionError",
    "TokenType",
    "StringLogger",
    "DebugLogger",
]
