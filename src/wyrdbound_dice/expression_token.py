from dataclasses import dataclass
from enum import Enum
from typing import Union


class TokenType(Enum):
    """Token types for mathematical expression parsing."""

    DICE = "DICE"
    NUMBER = "NUMBER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    EOF = "EOF"

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        return self.value


@dataclass(frozen=True)
class Token:
    """A token in a mathematical expression."""

    type: TokenType
    value: Union[str, int, None]
    position: int = 0

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        if self.value is None:
            return f"{self.type}@{self.position}"
        return f"{self.type}({self.value})@{self.position}"

    def is_operator(self) -> bool:
        """Check if this token represents an operator."""
        return self.type in {
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
        }

    def is_operand(self) -> bool:
        """Check if this token represents an operand."""
        return self.type in {TokenType.DICE, TokenType.NUMBER}
