from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestExpressionParsing(TestDiceBase):
    """Order of operations and expression parsing bug cases"""

    def test_order_of_operations_division_in_complex_expression(self):
        """Division now applies to immediate operand with proper precedence (FIXED!)."""
        self.mock_randint.side_effect = [7, 4, 1]
        r = Dice.roll("2d10 - 7 / 4 - 1d4")
        self.assertTotalAndDescription(
            r, 9, "9 = 11 (2d10: 7, 4) - (7 / 4) - 1 (1d4: 1)"
        )

    def test_order_of_operations_multiplication_and_division_chain(self):
        """Multiple multiplication/division operations now handled correctly (FIXED!)."""
        self.mock_randint.side_effect = [7]
        r = Dice.roll("1d10 / 2 x 2 + 5")
        self.assertTotalAndDescription(r, 11, "11 = 7 (1d10: 7) / 2 x 2 + 5")

    def test_multiple_operations_in_complex_expression(self):
        """Multiple multiplication operations in sequence now work correctly (FIXED!)."""
        self.mock_randint.side_effect = [4, 8, 2]
        r = Dice.roll("1d10 x 3 x 4 - 2d8")
        self.assertTotalAndDescription(
            r, 38, "38 = 4 (1d10: 4) x 3 x 4 - 10 (2d8: 8, 2)"
        )

    def test_division_in_mixed_expression(self):
        """Division correctly applies to its immediate operand (was already working)."""
        self.mock_randint.side_effect = [6, 4]
        r = Dice.roll("1d8 + 1d6 / 4")
        self.assertTotalAndDescription(r, 7, "7 = 6 (1d8: 6) + 4 (1d6: 4) / 4")

    def test_complex_math_expression_parsing_bug(self):
        """Complex expressions with multiple operations now parsed correctly (FIXED!)."""
        self.mock_randint.side_effect = [6, 8, 5]
        r = Dice.roll("2d8 - 1d6 - 1 x 4")
        self.assertTotalAndDescription(
            r, 5, "5 = 14 (2d8: 6, 8) - 5 (1d6: 5) - (1 x 4)"
        )

    def test_chained_multiplication_bug(self):
        """Multiple multiplication operations in sequence now handled correctly (FIXED!)."""
        self.mock_randint.side_effect = [10, 3]
        r = Dice.roll("2d10 x 2 x 4")
        self.assertTotalAndDescription(r, 104, "104 = 13 (2d10: 10, 3) x 2 x 4")

    def test_chained_division_and_multiplication_bug(self):
        """Chained division and multiplication operations now handled correctly (FIXED!)."""
        self.mock_randint.side_effect = [3]
        r = Dice.roll("1d20 / 2 / 3 x 2")
        self.assertTotalAndDescription(r, 0, "0 = 3 (1d20: 3) / 2 / 3 x 2")

    def test_expression_order_parsing_bug(self):
        """Expression components now parsed in correct mathematical order (FIXED!)."""
        self.mock_randint.side_effect = [8, 3]
        r = Dice.roll("1d10 - 5 + 1d6")
        self.assertTotalAndDescription(r, 6, "6 = 8 (1d10: 8) - 5 + 3 (1d6: 3)")


class TestMathematicalPrecedence(TestDiceBase):
    """Mathematical precedence tests to ensure they're followed correctly."""

    def test_mixed_operations_wrong_precedence_bug(self):
        """Mixed operations now follow mathematical precedence rules correctly."""
        self.mock_randint.side_effect = [1, 5]
        r = Dice.roll("2d6 + 7 x 4 x 2")
        self.assertTotalAndDescription(r, 62, "62 = 6 (2d6: 1, 5) + (7 x 4) x 2")
