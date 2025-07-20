from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceExplodingRerolls(TestDiceBase):
    def test_roll_exploding_dice(self):
        self.mock_randint.side_effect = [6, 3]
        r = Dice.roll("1d6e6")
        self.assertTotalAndDescription(r, 9, "9 = 9 (1d6e6: 6, 3)")

    def test_roll_exploding_dice_shorthand(self):
        self.mock_randint.side_effect = [6, 3]
        r = Dice.roll("1d6e")
        self.assertTotalAndDescription(r, 9, "9 = 9 (1d6e6: 6, 3)")

    def test_roll_exploding_dice_with_d10(self):
        self.mock_randint.side_effect = [10, 10, 2]
        r = Dice.roll("1d10e10")
        self.assertTotalAndDescription(r, 22, "22 = 22 (1d10e10: 10, 10, 2)")

    def test_roll_exploding_dice_with_d8(self):
        self.mock_randint.side_effect = [8, 8, 3]
        r = Dice.roll("1d8e")
        self.assertTotalAndDescription(r, 19, "19 = 19 (1d8e8: 8, 8, 3)")

    def test_roll_exploding_dice_with_d20(self):
        self.mock_randint.side_effect = [20, 20, 5]
        r = Dice.roll("1d20e20")
        self.assertTotalAndDescription(r, 45, "45 = 45 (1d20e20: 20, 20, 5)")

    def test_roll_exploding_dice_with_d4(self):
        self.mock_randint.side_effect = [4, 4, 2]
        r = Dice.roll("1d4e4")
        self.assertTotalAndDescription(r, 10, "10 = 10 (1d4e4: 4, 4, 2)")

    def test_roll_mutiple_exploding_dice(self):
        self.mock_randint.side_effect = [6, 6, 3, 6, 2]
        r = Dice.roll("2d6e6")
        self.assertTotalAndDescription(r, 23, "23 = 23 (2d6e6: 6, 6, 3, 6, 2)")

    def test_roll_more_exploding_dice(self):
        self.mock_randint.side_effect = [6, 6, 3, 6, 2, 4]
        r = Dice.roll("3d6e")
        self.assertTotalAndDescription(r, 27, "27 = 27 (3d6e6: 6, 6, 3, 6, 2, 4)")

    def test_roll_exploding_dice_with_mixed_modifiers(self):
        self.mock_randint.side_effect = [6, 6, 3]
        mods = {"Str Mod": 2}
        r = Dice.roll("1d6e + 2", modifiers=mods)
        self.assertTotalAndDescription(
            r, 19, "19 = 15 (1d6e6: 6, 6, 3) + 2 + 2 (Str Mod)"
        )

    def test_roll_exploding_dice_with_mixed_modifiers_and_dice_expression(self):
        self.mock_randint.side_effect = [6, 6, 3, 1, 2]
        mods = {"Str Mod": 2, "Prof Bonus": 3, "Bane": "-1d4", "Bless": "1d4"}
        r = Dice.roll("1d6e + 2", modifiers=mods)
        self.assertTotalAndDescription(
            r,
            23,
            "23 = 15 (1d6e6: 6, 6, 3) + 2 + 2 (Str Mod) + 3 (Prof Bonus) - 1 (Bane: 1 = 1 (1d4: 1)) + 2 (Bless: 2 = 2 (1d4: 2))",
        )

    def test_roll_exploding_dice_with_configurable_threshold(self):
        self.mock_randint.side_effect = [5, 6, 3]
        r = Dice.roll("1d6e>=5")
        self.assertTotalAndDescription(r, 14, "14 = 14 (1d6e>=5: 5, 6, 3)")
