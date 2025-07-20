from typing import Optional

from .errors import ParseError
from .expression_token import Token, TokenType


class UnicodeNormalizer:
    """Handles Unicode character normalization for dice expressions."""

    @staticmethod
    def normalize_unicode_chars(expression: str) -> str:
        """Normalize Unicode characters to ASCII equivalents."""
        result = ""
        for char in expression:
            normalized_char = UnicodeNormalizer._normalize_single_char(char)
            result += normalized_char
        return result

    @staticmethod
    def _normalize_single_char(char: str) -> str:
        """Normalize a single Unicode character."""
        # Convert fullwidth digits (U+FF10 to U+FF19) to ASCII
        if ord("０") <= ord(char) <= ord("９"):
            return chr(ord(char) - ord("０") + ord("0"))

        # Normalize unicode operators
        unicode_mappings = {
            "＋": "+",  # Fullwidth plus
            "−": "-",  # Unicode minus (U+2212)
            "×": "*",  # Unicode multiplication
            "÷": "/",  # Unicode division
        }

        return unicode_mappings.get(char, char)


class DiceExpressionReader:
    """Handles reading dice expressions from tokenized input."""

    def __init__(self, lexer: "ExpressionLexer"):
        self.lexer = lexer

    def read_dice_expression(self) -> str:
        """
        Read a complete dice expression like '2d6kh1r>=3e6',
        but not separate math operations.
        """
        start_pos = self.lexer.pos

        # Read the number of dice
        self._read_dice_count()

        # Must have 'd'
        if self.lexer.current_char != "d":
            raise ParseError(f"Invalid dice expression at position {self.lexer.pos}")
        self.lexer.advance()

        # Read sides (number or 'F' for fudge)
        self._read_dice_sides()

        # Read optional dice-specific modifiers
        self._read_dice_modifiers()

        return self.lexer.expr[start_pos : self.lexer.pos]

    def _read_dice_count(self) -> None:
        """Read the number of dice."""
        while self.lexer.current_char is not None and self.lexer.current_char.isdigit():
            self.lexer.advance()

    def _read_dice_sides(self) -> None:
        """Read dice sides (number or 'F' for fudge)."""
        if self.lexer.current_char and self.lexer.current_char.lower() == "f":
            self.lexer.advance()
        else:
            while (
                self.lexer.current_char is not None
                and self.lexer.current_char.isdigit()
            ):
                self.lexer.advance()

    def _read_dice_modifiers(self) -> None:
        """
        Read optional dice-specific modifiers:
        keep (k), reroll (r), explode (e).
        """
        while self.lexer.current_char is not None:
            if self.lexer.current_char == "k":
                self._read_keep_modifier()
            elif self.lexer.current_char == "r":
                self._read_reroll_modifier()
            elif self.lexer.current_char == "e":
                self._read_explode_modifier()
            else:
                # Stop at any other character (including math operators)
                break

    def _read_keep_modifier(self) -> None:
        """Read keep modifier: kh2, kl1, etc."""
        self.lexer.advance()
        if self.lexer.current_char in "hl":
            self.lexer.advance()
        while self.lexer.current_char is not None and self.lexer.current_char.isdigit():
            self.lexer.advance()

    def _read_reroll_modifier(self) -> None:
        """Read reroll modifier: r>=3, r=1, etc."""
        self.lexer.advance()
        # Read optional count (number or 'o' for once)
        while self.lexer.current_char is not None and (
            self.lexer.current_char.isdigit() or self.lexer.current_char == "o"
        ):
            self.lexer.advance()
        # Read comparison operator
        if self.lexer.current_char in "=<>":
            while self.lexer.current_char in "=<>":
                self.lexer.advance()
        # Read target number
        while self.lexer.current_char is not None and self.lexer.current_char.isdigit():
            self.lexer.advance()

    def _read_explode_modifier(self) -> None:
        """Read exploding dice modifier: e>=8, e6, etc."""
        self.lexer.advance()
        # Read optional comparison operator
        if self.lexer.current_char is not None and self.lexer.current_char in "=<>":
            while (
                self.lexer.current_char is not None and self.lexer.current_char in "=<>"
            ):
                self.lexer.advance()
        # Read target number
        while self.lexer.current_char is not None and self.lexer.current_char.isdigit():
            self.lexer.advance()


class ExpressionLexer:
    """Tokenizes dice expressions with proper mathematical operators."""

    @staticmethod
    def normalize_unicode_chars(expression: str) -> str:
        """Normalize Unicode characters to ASCII equivalents."""
        return UnicodeNormalizer.normalize_unicode_chars(expression)

    def __init__(self, expression: str):
        normalized_expr = self.normalize_unicode_chars(expression)
        # Remove spaces for easier parsing
        self.expr = normalized_expr.replace(" ", "")
        self.pos = 0
        self.current_char = self.expr[self.pos] if self.pos < len(self.expr) else None
        self.dice_reader = DiceExpressionReader(self)

    def advance(self) -> None:
        """Move to the next character."""
        self.pos += 1
        if self.pos >= len(self.expr):
            self.current_char = None
        else:
            self.current_char = self.expr[self.pos]

    def peek(self, offset: int = 1) -> Optional[str]:
        """Look ahead at the next character without advancing."""
        peek_pos = self.pos + offset
        if peek_pos >= len(self.expr):
            return None
        return self.expr[peek_pos]

    def read_number(self) -> int:
        """Read a number from the current position."""
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def read_dice_expression(self) -> str:
        """Read a complete dice expression using the DiceExpressionReader."""
        return self.dice_reader.read_dice_expression()

    def get_next_token(self) -> Token:
        """Get the next token from the expression."""
        while self.current_char is not None:
            if self.current_char.isspace():
                self.advance()
                continue

            if self.current_char.isdigit():
                return self._handle_digit_token()

            # Handle operators and special characters
            operator_token = self._handle_operator_token()
            if operator_token:
                return operator_token

            raise ParseError(
                f"Invalid character '{self.current_char}' at " + f"position {self.pos}"
            )

        return Token(TokenType.EOF, None, self.pos)

    def _handle_digit_token(self) -> Token:
        """Handle digit tokens (numbers or dice expressions)."""
        # Check if this is a dice expression (number followed by 'd')
        if self.peek() == "d":
            dice_expr = self.read_dice_expression()
            return Token(TokenType.DICE, dice_expr, self.pos - len(dice_expr))
        else:
            # Regular number
            number = self.read_number()
            return Token(TokenType.NUMBER, number, self.pos - len(str(number)))

    def _handle_operator_token(self) -> Optional[Token]:
        """Handle operator and special character tokens."""
        char = self.current_char
        pos = self.pos

        if char in ["+", "＋"]:  # Include fullwidth plus
            self.advance()
            return Token(TokenType.PLUS, "+", pos)

        if char in ["-", "−"]:  # Include unicode minus (U+2212)
            self.advance()
            return Token(TokenType.MINUS, "-", pos)

        if char in ["x", "*", "Ã", "×"]:  # Include unicode multiplication
            self.advance()
            return Token(TokenType.MULTIPLY, "x", pos)

        if char in ["/", "÷"]:  # Include unicode division
            self.advance()
            return Token(TokenType.DIVIDE, "/", pos)

        if char == "(":
            self.advance()
            return Token(TokenType.LPAREN, "(", pos)

        if char == ")":
            self.advance()
            return Token(TokenType.RPAREN, ")", pos)

        return None
