from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceFudge(TestDiceBase):
    def test_roll_single_fudge_dice(self):
        self.mock_randint.side_effect = [1]
        r = Dice.roll("1dF")
        self.assertTotalAndDescription(r, -1, "-1 = -1 (1dF: -)")

    def test_roll_multiple_fudge_dice(self):
        self.mock_randint.side_effect = [1, 3, 4, 6]
        r = Dice.roll("4dF")
        self.assertTotalAndDescription(r, 0, "0 = 0 (4dF: -, B, B, +)")

    def test_roll_fudge_dice_with_modifiers(self):
        self.mock_randint.side_effect = [1, 3, 4, 6]
        mods = {"Party Assist": 1}
        r = Dice.roll("4dF + 1", modifiers=mods)
        self.assertTotalAndDescription(
            r, 2, "2 = 0 (4dF: -, B, B, +) + 1 + 1 (Party Assist)"
        )

    def test_roll_fudge_dice_with_negative_modifiers(self):
        self.mock_randint.side_effect = [1, 3, 4, 6]
        mods = {"Disadvantage": -1}
        r = Dice.roll("4dF", modifiers=mods)
        self.assertTotalAndDescription(
            r, -1, "-1 = 0 (4dF: -, B, B, +) - 1 (Disadvantage)"
        )

    def test_roll_multiple_fudge_rolls(self):
        self.mock_randint.side_effect = [1, 3, 4, 6, 2, 5, 1, 4]
        r = Dice.roll("4dF + 4dF")
        self.assertTotalAndDescription(
            r, -1, "-1 = 0 (4dF: -, B, B, +) - 1 (4dF: -, +, -, B)"
        )
