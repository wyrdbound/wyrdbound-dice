from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceUnicodeAndSpecialCharacters(TestDiceBase):
    def test_unicode_multiplication_symbol(self):
        """Test unicode multiplication symbol × in expressions."""
        self.mock_randint.side_effect = [2]
        result = Dice.roll("1d6×3")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(result, 6, "6 = 2 (1d6: 2) x 3")

    def test_unicode_division_symbol(self):
        """Test unicode division symbol ÷ in expressions."""
        self.mock_randint.side_effect = [2]
        result = Dice.roll("1d6÷2")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(result, 1, "1 = 2 (1d6: 2) / 2")

    def test_unicode_minus_sign(self):
        """Test unicode minus sign − (U+2212) in expressions."""
        self.mock_randint.side_effect = [2]
        result = Dice.roll("1d6−1")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(result, 1, "1 = 2 (1d6: 2) - 1")

    def test_unicode_fullwidth_plus_sign(self):
        """Test fullwidth plus sign ＋ in expressions."""
        self.mock_randint.side_effect = [2]
        result = Dice.roll("1d6＋1")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(result, 3, "3 = 2 (1d6: 2) + 1")

    def test_unicode_fullwidth_digit_in_count(self):
        """Test fullwidth digit １ in dice count."""
        self.mock_randint.side_effect = [2]
        result = Dice.roll("１d6")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(result, 2, "2 = 2 (1d6: 2)")

    def test_unicode_fullwidth_digit_in_sides(self):
        """Test fullwidth digit ６ in dice sides."""
        self.mock_randint.side_effect = [2]
        result = Dice.roll("1d６")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(result, 2, "2 = 2 (1d6: 2)")
