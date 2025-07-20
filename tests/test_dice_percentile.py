from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDicePercentile(TestDiceBase):
    def test_percentile_roll(self):
        self.mock_randint.side_effect = [8, 6]
        r = Dice.roll("1d%")
        self.assertTotalAndDescription(r, 86, "86 = 86 (1d%: [80, 6])")

    def test_percentile_roll_min_value(self):
        self.mock_randint.side_effect = [0, 1]
        r = Dice.roll("1d%")
        self.assertTotalAndDescription(r, 1, "1 = 1 (1d%: [00, 1])")

    def test_percentile_roll_max_value(self):
        self.mock_randint.side_effect = [0, 0]
        r = Dice.roll("1d%")
        self.assertTotalAndDescription(r, 100, "100 = 100 (1d%: [00, 0])")

    def test_percentile_keep_highest(self):
        self.mock_randint.side_effect = [0, 5, 8, 6]
        r = Dice.roll("2d%kh1")
        self.assertTotalAndDescription(r, 86, "86 = 86 (2d%kh1: [00, 5], [80, 6])")

    def test_percentile_reroll(self):
        self.mock_randint.side_effect = [0, 5, 3, 7, 5, 1, 4, 3, 8, 4]
        r = Dice.roll("2d%r<50")
        self.assertTotalAndDescription(
            r, 135, "135 = 135 (2d%r<50: [00, 5], [30, 7], [50, 1], [40, 3], [80, 4])"
        )

    def test_percentile_multi_dice_keep_highest(self):
        self.mock_randint.side_effect = [0, 5, 3, 7, 8, 6, 5, 1]
        r = Dice.roll("4d%kh2")
        self.assertTotalAndDescription(
            r, 137, "137 = 137 (4d%kh2: [00, 5], [30, 7], [80, 6], [50, 1])"
        )
