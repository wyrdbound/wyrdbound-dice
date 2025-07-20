from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceKeepHighestLowest(TestDiceBase):
    def test_roll_keep_highest(self):
        self.mock_randint.side_effect = [3, 1, 5, 6]
        r = Dice.roll("4d6 kh 3")
        self.assertEqual(r.subtotal, 14)
        self.assertTotalAndDescription(r, 14, "14 = 14 (4d6kh3: 3, 1, 5, 6)")

    def test_roll_keep_highest_no_spaces(self):
        self.mock_randint.side_effect = [3, 1, 5, 6]
        r = Dice.roll("4d6kh3")
        self.assertEqual(r.subtotal, 14)
        self.assertTotalAndDescription(r, 14, "14 = 14 (4d6kh3: 3, 1, 5, 6)")

    def test_roll_keep_lowest(self):
        self.mock_randint.side_effect = [19, 8]
        r = Dice.roll("2d20 kl 1")
        self.assertEqual(r.subtotal, 8)
        self.assertTotalAndDescription(r, 8, "8 = 8 (2d20kl1: 19, 8)")

    def test_roll_keep_lowest_no_spaces(self):
        self.mock_randint.side_effect = [19, 8]
        r = Dice.roll("2d20kl1")
        self.assertEqual(r.subtotal, 8)
        self.assertTotalAndDescription(r, 8, "8 = 8 (2d20kl1: 19, 8)")

    def test_roll_keep_highest_with_shorthand_for_one(self):
        self.mock_randint.side_effect = [3, 1, 5, 6]
        r = Dice.roll("4d6kh")
        self.assertEqual(r.subtotal, 6)
        self.assertTotalAndDescription(r, 6, "6 = 6 (4d6kh1: 3, 1, 5, 6)")

    def test_roll_keep_lowest_with_shorthand_for_one(self):
        self.mock_randint.side_effect = [3, 1, 5, 6]
        r = Dice.roll("4d6kl")
        self.assertEqual(r.subtotal, 1)
        self.assertTotalAndDescription(r, 1, "1 = 1 (4d6kl1: 3, 1, 5, 6)")
