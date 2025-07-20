from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceReroll(TestDiceBase):
    def test_roll_reroll_once(self):
        self.mock_randint.side_effect = [1, 5]
        r = Dice.roll("1d6r1<=2")
        self.assertTotalAndDescription(r, 5, "5 = 5 (1d6r1<=2: 1, 5)")

    def test_roll_reroll_once_alternate_notation(self):
        self.mock_randint.side_effect = [1, 5]
        r = Dice.roll("1d6ro<=2")
        self.assertTotalAndDescription(r, 5, "5 = 5 (1d6ro<=2: 1, 5)")

    def test_roll_reroll_once_not_better(self):
        self.mock_randint.side_effect = [2, 1]
        r = Dice.roll("1d6r1<3")
        self.assertTotalAndDescription(r, 1, "1 = 1 (1d6r1<3: 2, 1)")

    def test_roll_unlimited_reroll(self):
        self.mock_randint.side_effect = [1, 2, 1, 4]
        r = Dice.roll("1d6r<=2")
        self.assertTotalAndDescription(r, 4, "4 = 4 (1d6r<=2: 1, 2, 1, 4)")

    def test_roll_reroll_thrice_limit(self):
        self.mock_randint.side_effect = [1, 1, 2, 3]
        r = Dice.roll("1d6r3<=3")
        self.assertTotalAndDescription(r, 3, "3 = 3 (1d6r3<=3: 1, 1, 2, 3)")

    def test_roll_reroll_multiple_dice(self):
        self.mock_randint.side_effect = [1, 6, 2, 3]
        r = Dice.roll("2d6r1<=2")
        self.assertTotalAndDescription(r, 9, "9 = 9 (2d6r1<=2: 1, 6, 2, 3)")
