"""Custom exception classes for dice expression parsing and evaluation."""

from typing import Optional


class DiceExpressionError(ValueError):
    """Base class for all dice expression related errors."""

    pass


class InfiniteConditionError(DiceExpressionError):
    """Raised when a dice condition would create an infinite loop."""

    def __init__(self, condition_type: str, expression: str, reason: str):
        self.condition_type = condition_type
        self.expression = expression
        self.reason = reason
        super().__init__(
            f"Infinite {condition_type} condition in '{expression}': {reason}"
        )


class DivisionByZeroError(DiceExpressionError):
    """Raised when division by zero is attempted in dice expressions."""

    def __init__(self, expression: Optional[str] = None):
        self.expression = expression
        message = "Division by zero"
        if expression:
            message += f" in expression '{expression}'"
        super().__init__(message)


class ParseError(DiceExpressionError):
    """Raised when parsing fails in dice expression parsers."""

    def __init__(self, message: str, position: Optional[int] = None):
        self.position = position
        if position is not None:
            message += f" at position {position}"
        super().__init__(message)
