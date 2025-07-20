import sys
from pathlib import Path

# Add the src directory to the path so we can import wyrdbound_dice
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDice(TestDiceBase):
    def test_roll_basic_dice(self):
        self.mock_randint.side_effect = [4]
        r = Dice.roll("1d6")
        self.assertTotalAndDescription(r, 4, "4 = 4 (1d6: 4)")

    def test_roll_multiple_dice(self):
        self.mock_randint.side_effect = [2, 3, 5]
        r = Dice.roll("3d6")
        self.assertTotalAndDescription(r, 10, "10 = 10 (3d6: 2, 3, 5)")


class TestDiceMultipleRolls(TestDiceBase):
    def test_roll_sum_two_different_dice(self):
        self.mock_randint.side_effect = [3, 4, 5, 6]
        r = Dice.roll("2d6 + 2d8")
        self.assertTotalAndDescription(r, 18, "18 = 7 (2d6: 3, 4) + 11 (2d8: 5, 6)")

    def test_roll_subtract_two_different_dice(self):
        self.mock_randint.side_effect = [14, 3]
        r = Dice.roll("1d20 - 1d4")
        self.assertTotalAndDescription(r, 11, "11 = 14 (1d20: 14) - 3 (1d4: 3)")

    def test_roll_multiple_subtractions(self):
        self.mock_randint.side_effect = [20, 2, 1]
        r = Dice.roll("1d20 - 1d4 - 1d6")
        self.assertTotalAndDescription(
            r, 17, "17 = 20 (1d20: 20) - 2 (1d4: 2) - 1 (1d6: 1)"
        )

    def test_roll_mixed_operations(self):
        self.mock_randint.side_effect = [10, 5, 3]
        r = Dice.roll("1d20 + 1d6 - 1d4")
        self.assertTotalAndDescription(
            r, 12, "12 = 10 (1d20: 10) + 5 (1d6: 5) - 3 (1d4: 3)"
        )

    def test_roll_subtraction_with_modifiers(self):
        self.mock_randint.side_effect = [15, 2]
        r = Dice.roll("1d20 - 1d4 + 3")
        self.assertTotalAndDescription(r, 16, "16 = 15 (1d20: 15) - 2 (1d4: 2) + 3")


class TestDiceMultiplication(TestDiceBase):
    def test_roll_multiply_dice(self):
        self.mock_randint.side_effect = [4]
        r = Dice.roll("1d6 x 3")
        self.assertTotalAndDescription(r, 12, "12 = 4 (1d6: 4) x 3")

    def test_roll_multiply_dice_no_space(self):
        self.mock_randint.side_effect = [4]
        r = Dice.roll("1d6x3")
        self.assertTotalAndDescription(r, 12, "12 = 4 (1d6: 4) x 3")

    def test_roll_multiply_dice_multiplication_symbol(self):
        self.mock_randint.side_effect = [3]
        r = Dice.roll("1d6 × 3")
        self.assertTotalAndDescription(r, 9, "9 = 3 (1d6: 3) x 3")

    def test_roll_multiply_dice_no_space_multiplication_symbol(self):
        self.mock_randint.side_effect = [3]
        r = Dice.roll("1d6×3")
        self.assertTotalAndDescription(r, 9, "9 = 3 (1d6: 3) x 3")

    def test_roll_multiply_multiple_dice(self):
        self.mock_randint.side_effect = [7, 3, 9]
        r = Dice.roll("3d10 x 10")
        self.assertTotalAndDescription(r, 190, "190 = 19 (3d10: 7, 3, 9) x 10")

    def test_roll_multiply_multiple_dice_rolls(self):
        self.mock_randint.side_effect = [7, 3, 9, 2]
        r = Dice.roll("3d10 x 1d6")
        self.assertTotalAndDescription(r, 38, "38 = 19 (3d10: 7, 3, 9) x 2 (1d6: 2)")

    def test_roll_multiply_multiple_dice_rolls_multiplication_symbol(self):
        self.mock_randint.side_effect = [7, 3, 9, 3]
        r = Dice.roll("3d10 × 1d6")
        self.assertTotalAndDescription(r, 57, "57 = 19 (3d10: 7, 3, 9) x 3 (1d6: 3)")


class TestDiceDivision(TestDiceBase):
    def test_roll_divide_dice(self):
        self.mock_randint.side_effect = [4]
        r = Dice.roll("1d6 / 2")
        self.assertTotalAndDescription(r, 2, "2 = 4 (1d6: 4) / 2")

    def test_roll_divide_dice_no_space(self):
        self.mock_randint.side_effect = [4]
        r = Dice.roll("1d6/2")
        self.assertTotalAndDescription(r, 2, "2 = 4 (1d6: 4) / 2")

    def test_roll_divide_dice_division_symbol(self):
        self.mock_randint.side_effect = [4]
        r = Dice.roll("1d6 ÷ 2")
        self.assertTotalAndDescription(r, 2, "2 = 4 (1d6: 4) / 2")

    def test_roll_divide_dice_no_space_division_symbol(self):
        self.mock_randint.side_effect = [4]
        r = Dice.roll("1d6÷2")
        self.assertTotalAndDescription(r, 2, "2 = 4 (1d6: 4) / 2")

    def test_roll_divide_multiple_dice(self):
        self.mock_randint.side_effect = [7, 3, 9]
        r = Dice.roll("3d10 / 10")
        self.assertTotalAndDescription(r, 1, "1 = 19 (3d10: 7, 3, 9) / 10")

    def test_roll_divide_multiple_dice_rolls(self):
        self.mock_randint.side_effect = [7, 3, 9, 2]
        r = Dice.roll("3d10 / 1d4")
        self.assertTotalAndDescription(r, 9, "9 = 19 (3d10: 7, 3, 9) / 2 (1d4: 2)")

    def test_roll_divide_multiple_dice_rolls_division_symbol(self):
        self.mock_randint.side_effect = [7, 3, 9, 2]
        r = Dice.roll("3d10 ÷ 1d4")
        self.assertTotalAndDescription(r, 9, "9 = 19 (3d10: 7, 3, 9) / 2 (1d4: 2)")
