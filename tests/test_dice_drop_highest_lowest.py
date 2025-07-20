from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceDropHighestLowest(TestDiceBase):
    def test_roll_drop_highest(self):
        self.mock_randint.side_effect = [3, 1, 5, 6]
        r = Dice.roll("4d6 dh 3")
        self.assertEqual(r.subtotal, 1)
        self.assertTotalAndDescription(r, 1, "1 = 1 (4d6dh3: 3, 1, 5, 6)")

    def test_roll_drop_highest_no_spaces(self):
        self.mock_randint.side_effect = [3, 1, 5, 6]
        r = Dice.roll("4d6dh3")
        self.assertTotalAndDescription(r, 1, "1 = 1 (4d6dh3: 3, 1, 5, 6)")

    def test_roll_drop_lowest(self):
        self.mock_randint.side_effect = [19, 8]
        r = Dice.roll("2d20 dl 1")
        self.assertTotalAndDescription(r, 19, "19 = 19 (2d20dl1: 19, 8)")

    def test_roll_drop_lowest_no_spaces(self):
        self.mock_randint.side_effect = [19, 8]
        r = Dice.roll("2d20dl1")
        self.assertTotalAndDescription(r, 19, "19 = 19 (2d20dl1: 19, 8)")

    def test_roll_drop_highest_with_shorthand_for_one(self):
        self.mock_randint.side_effect = [3, 1, 5, 6]
        r = Dice.roll("4d6dh")
        self.assertTotalAndDescription(r, 9, "9 = 9 (4d6dh1: 3, 1, 5, 6)")

    def test_roll_drop_lowest_with_shorthand_for_one(self):
        self.mock_randint.side_effect = [3, 1, 5, 6]
        r = Dice.roll("4d6dl")
        self.assertTotalAndDescription(r, 14, "14 = 14 (4d6dl1: 3, 1, 5, 6)")
