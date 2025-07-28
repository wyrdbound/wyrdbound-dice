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

from .debug_logger import DebugLogger, StringLogger
from .dice import Dice, RollModifier, RollResultSet
from .errors import DivisionByZeroError, InfiniteConditionError, ParseError
from .expression_token import TokenType
from .roll_result import RollResult

__version__ = "0.0.1"
__author__ = "The Wyrd One"
__email__ = "wyrdbound@proton.me"
__description__ = "A comprehensive dice rolling library for tabletop RPGs"


# Convenience function for easier access
def roll(expression, modifiers=None, debug=False, debug_logger=None):
    """Convenience function for rolling dice.

    Args:
        expression (str): The dice expression to roll
        modifiers: Optional additional modifiers as a dictionary
        debug: Enable debug logging to see detailed parsing and rolling steps
        debug_logger: Optional debug logger instance (replaces 'logger'
            parameter)

    Returns:
        RollResult: The result of the dice roll
    """
    return Dice.roll(expression, modifiers, debug, debug_logger)


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
    "roll",
]
