from dataclasses import dataclass
from typing import List, Tuple

from .errors import DivisionByZeroError, ParseError
from .expression_token import Token, TokenType
from .roll_result import RollResult


@dataclass
class EvaluationResult:
    """Result of evaluating a parsed expression."""

    value: int
    description: str
    dice_results: List["RollResult"]


class OperatorHandler:
    """Handles evaluation of different operators."""

    @staticmethod
    def evaluate_binary_operation(
        left_val: int, right_val: int, operator: TokenType
    ) -> Tuple[int, str]:
        """Evaluate a binary operation and return (result, symbol)."""
        if operator == TokenType.PLUS:
            return left_val + right_val, "+"
        elif operator == TokenType.MINUS:
            return left_val - right_val, "-"
        elif operator == TokenType.MULTIPLY:
            return left_val * right_val, "x"
        elif operator == TokenType.DIVIDE:
            if right_val == 0:
                raise DivisionByZeroError()
            return left_val // right_val, "/"  # Integer division
        else:
            raise ParseError(f"Unknown operator: {operator}")


class DescriptionBuilder:
    """Builds description strings for expressions."""

    @staticmethod
    def build_binary_description(
        left_result: EvaluationResult,
        right_result: EvaluationResult,
        operator: TokenType,
        op_symbol: str,
    ) -> str:
        """Build description for binary operations with proper formatting."""
        # Handle simple number calculations
        if not left_result.dice_results and not right_result.dice_results:
            # For multiplication and division, preserve the chain structure by
            # showing original expressions unless we need parentheses for
            # clarity
            if operator in [TokenType.MULTIPLY, TokenType.DIVIDE]:
                # If both operands are simple numbers (not expressions), add
                # parentheses
                if (
                    left_result.description.isdigit()
                    or (
                        left_result.description.startswith("-")
                        and left_result.description[1:].isdigit()
                    )
                ) and (
                    right_result.description.isdigit()
                    or (
                        right_result.description.startswith("-")
                        and right_result.description[1:].isdigit()
                    )
                ):
                    return (
                        f"({left_result.description} {op_symbol} "
                        + f"{right_result.description})"
                    )
                else:
                    # Preserve the chain structure without extra parentheses
                    return (
                        f"{left_result.description} {op_symbol} "
                        + f"{right_result.description}"
                    )
            else:
                return (
                    f"{left_result.description} {op_symbol} "
                    + f"{right_result.description}"
                )

        # Handle negative values in addition/subtraction
        if operator == TokenType.PLUS and right_result.value < 0:
            # Change "A + -B" to "A - B"
            positive_right_desc = DescriptionBuilder._remove_leading_minus(
                right_result.description
            )
            return f"{left_result.description} - {positive_right_desc}"
        elif operator == TokenType.MINUS and right_result.value < 0:
            # Change "A - -B" to "A + B"
            positive_right_desc = DescriptionBuilder._remove_leading_minus(
                right_result.description
            )
            return f"{left_result.description} + {positive_right_desc}"
        else:
            return (
                f"{left_result.description} {op_symbol} "
                + f"{right_result.description}"
            )

    @staticmethod
    def _remove_leading_minus(description: str) -> str:
        """Remove leading minus sign from description."""
        return description[1:] if description.startswith("-") else description


class ExpressionParser:
    """
    Parses tokenized dice expressions with proper mathematical
    precedence.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else Token(TokenType.EOF, None)

    def advance(self) -> None:
        """Move to the next token."""
        self.pos += 1
        if self.pos >= len(self.tokens):
            self.current_token = Token(TokenType.EOF, None)
        else:
            self.current_token = self.tokens[self.pos]

    def parse(self) -> "ParsedExpression":
        """Parse the tokens into an expression tree with proper precedence."""
        result = self.parse_expression()
        if self.current_token.type != TokenType.EOF:
            raise ParseError(f"Unexpected token: {self.current_token}")
        return result

    def parse_expression(self) -> "ParsedExpression":
        """Parse addition and subtraction (lowest precedence)."""
        left = self.parse_term()

        while self.current_token.type in [TokenType.PLUS, TokenType.MINUS]:
            op = self.current_token.type
            self.advance()
            right = self.parse_term()
            left = BinaryOperation(left, op, right)

        return left

    def parse_term(self) -> "ParsedExpression":
        """Parse multiplication and division (higher precedence)."""
        left = self.parse_factor()

        while self.current_token.type in [
            TokenType.MULTIPLY,
            TokenType.DIVIDE,
        ]:
            op = self.current_token.type
            self.advance()
            right = self.parse_factor()
            left = BinaryOperation(left, op, right)

        return left

    def parse_factor(self) -> "ParsedExpression":
        """Parse factors (numbers, dice, parentheses)."""
        token = self.current_token

        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberExpression(token.value)

        if token.type == TokenType.DICE:
            self.advance()
            return DiceExpression(token.value)

        if token.type == TokenType.MINUS:
            self.advance()
            factor = self.parse_factor()
            return UnaryOperation(TokenType.MINUS, factor)

        if token.type == TokenType.PLUS:
            self.advance()
            factor = self.parse_factor()
            return factor  # Unary plus doesn't change the value

        if token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            if self.current_token.type != TokenType.RPAREN:
                raise ParseError("Missing closing parenthesis")
            self.advance()
            return expr

        raise ParseError(f"Unexpected token: {token}")


# Expression tree node classes
class ParsedExpression:
    """Base class for parsed expression nodes."""

    def evaluate(self, dice_class) -> EvaluationResult:
        """Evaluate this expression node."""
        raise NotImplementedError


class NumberExpression(ParsedExpression):
    """A constant number in the expression."""

    def __init__(self, value: int):
        self.value = value

    def evaluate(self, dice_class) -> EvaluationResult:
        return EvaluationResult(
            value=self.value, description=str(self.value), dice_results=[]
        )


class DiceExpression(ParsedExpression):
    """A dice expression like '2d6' or '1d20kh1'."""

    def __init__(self, dice_expr: str):
        self.dice_expr = dice_expr

    def evaluate(self, dice_class) -> EvaluationResult:
        # Use the existing dice rolling logic
        result = dice_class._roll_single_dice_expression_from_string(self.dice_expr)
        return EvaluationResult(
            value=result.subtotal,
            description=str(result),
            dice_results=[result],
        )


class BinaryOperation(ParsedExpression):
    """
    A binary operation like addition, subtraction, multiplication,
    or division.
    """

    def __init__(
        self,
        left: ParsedExpression,
        operator: TokenType,
        right: ParsedExpression,
    ):
        self.left = left
        self.operator = operator
        self.right = right

    def evaluate(self, dice_class) -> EvaluationResult:
        left_result = self.left.evaluate(dice_class)
        right_result = self.right.evaluate(dice_class)

        # Perform the operation
        value, op_symbol = OperatorHandler.evaluate_binary_operation(
            left_result.value, right_result.value, self.operator
        )

        # Build description
        description = DescriptionBuilder.build_binary_description(
            left_result, right_result, self.operator, op_symbol
        )

        # Combine dice results
        dice_results = left_result.dice_results + right_result.dice_results

        return EvaluationResult(
            value=value, description=description, dice_results=dice_results
        )


class UnaryOperation(ParsedExpression):
    """A unary operation like negation."""

    def __init__(self, operator: TokenType, operand: ParsedExpression):
        self.operator = operator
        self.operand = operand

    def evaluate(self, dice_class) -> EvaluationResult:
        operand_result = self.operand.evaluate(dice_class)

        if self.operator == TokenType.MINUS:
            value = -operand_result.value
            description = f"-{operand_result.description}"
        else:
            raise ParseError(f"Unknown unary operator: {self.operator}")

        return EvaluationResult(
            value=value,
            description=description,
            dice_results=operand_result.dice_results,
        )
