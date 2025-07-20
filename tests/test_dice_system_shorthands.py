from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceSystemShorthands(TestDiceBase):
    def test_roll_fudge_shorthand(self):
        self.mock_randint.side_effect = [6, 5, 1, 3]
        r = Dice.roll("FUDGE")
        self.assertTotalAndDescription(r, 1, "1 = 1 (4dF: +, +, -, B)")

    def test_roll_boon_shorthand(self):
        self.mock_randint.side_effect = [6, 3, 1]
        r = Dice.roll("BOON")
        self.assertTotalAndDescription(r, 9, "9 = 9 (3d6kh2: 6, 3, 1)")

    def test_roll_bane_shorthand(self):
        self.mock_randint.side_effect = [6, 3, 1]
        r = Dice.roll("BANE")
        self.assertTotalAndDescription(r, 4, "4 = 4 (3d6kl2: 6, 3, 1)")

    def test_roll_flux_shorthand(self):
        self.mock_randint.side_effect = [3, 2]
        r = Dice.roll("FLUX")
        self.assertTotalAndDescription(r, 1, "1 = 3 (1d6: 3) - 2 (1d6: 2)")

    def test_roll_goodflux_shorthand_highest_first(self):
        self.mock_randint.side_effect = [6, 5]
        r = Dice.roll("GOODFLUX")
        self.assertTotalAndDescription(r, 1, "1 = 6 (1d6: 6) - 5 (1d6: 5)")

    def test_roll_goodflux_shorthand_lowest_first(self):
        self.mock_randint.side_effect = [5, 6]
        r = Dice.roll("GOODFLUX")
        self.assertTotalAndDescription(r, 1, "1 = 6 (1d6: 6) - 5 (1d6: 5)")

    def test_roll_badflux_shorthand_highest_first(self):
        self.mock_randint.side_effect = [6, 5]
        r = Dice.roll("BADFLUX")
        self.assertTotalAndDescription(r, -1, "-1 = 5 (1d6: 5) - 6 (1d6: 6)")

    def test_roll_badflux_shorthand_lowest_first(self):
        self.mock_randint.side_effect = [5, 6]
        r = Dice.roll("BADFLUX")
        self.assertTotalAndDescription(r, -1, "-1 = 5 (1d6: 5) - 6 (1d6: 6)")

    def test_roll_goodflux_table(self):
        for i in range(1, 7):
            self.mock_randint.side_effect = [i, 6]
            r = Dice.roll("GOODFLUX")
            self.assertTotalAndDescription(
                r, 6 - i, f"{6 - i} = 6 (1d6: 6) - {i} (1d6: {i})"
            )

    def test_roll_badflux_table(self):
        for i in range(1, 7):
            self.mock_randint.side_effect = [i, 6]
            r = Dice.roll("BADFLUX")
            self.assertTotalAndDescription(
                r, i - 6, f"{i - 6} = {i} (1d6: {i}) - 6 (1d6: 6)"
            )

    def test_percentile_shorthands(self):
        self.mock_randint.side_effect = [9, 3]
        r = Dice.roll("PERC")
        self.assertTotalAndDescription(r, 93, "93 = 93 (1d%: [90, 3])")

        self.mock_randint.side_effect = [0, 5]
        r = Dice.roll("PERCENTILE")
        self.assertTotalAndDescription(r, 5, "5 = 5 (1d%: [00, 5])")
