from dataclasses import dataclass
from typing import List, Tuple

from .breakdown import BinaryOp, DiceNode, Literal, Node, UnaryOp
from .errors import DivisionByZeroError, ParseError
from .expression_token import Token, TokenType
from .formatting import DefaultFormatter, RollFormat
from .roll_result import RollResult


@dataclass
class EvaluationResult:
    """Result of evaluating a parsed expression."""

    value: int
    node: Node
    dice_results: List["RollResult"]

    @property
    def description(self) -> str:
        """Render this result's node with the standard formatter."""
        return DefaultFormatter(RollFormat(layout="{breakdown}")).format_node(self.node)


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
            value=self.value, node=Literal(self.value), dice_results=[]
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
            node=DiceNode(result.breakdown),
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

        # Combine dice results
        dice_results = left_result.dice_results + right_result.dice_results

        node = BinaryOp(left_result.node, op_symbol, right_result.node, value)

        return EvaluationResult(value=value, node=node, dice_results=dice_results)


class UnaryOperation(ParsedExpression):
    """A unary operation like negation."""

    def __init__(self, operator: TokenType, operand: ParsedExpression):
        self.operator = operator
        self.operand = operand

    def evaluate(self, dice_class) -> EvaluationResult:
        operand_result = self.operand.evaluate(dice_class)

        if self.operator == TokenType.MINUS:
            value = -operand_result.value
            node = UnaryOp("-", operand_result.node, value)
        else:
            raise ParseError(f"Unknown unary operator: {self.operator}")

        return EvaluationResult(
            value=value,
            node=node,
            dice_results=operand_result.dice_results,
        )
