from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceZeroDiceEdgeCases(TestDiceBase):
    def test_zero_dice_basic(self):
        """Test basic zero dice."""
        result = Dice.roll("0d6")
        self.assertTotalAndDescription(result, 0, "0 = 0 (0d6)")

    def test_zero_dice_with_keep(self):
        """Test zero dice with keep."""
        result = Dice.roll("0d6kh1")
        self.assertTotalAndDescription(result, 0, "0 = 0 (0d6kh1)")

    def test_zero_dice_with_reroll(self):
        """Test zero dice with reroll."""
        result = Dice.roll("0d6r<=2")
        self.assertTotalAndDescription(result, 0, "0 = 0 (0d6r<=2)")

    def test_zero_dice_with_explode(self):
        """Test zero dice with explode."""
        result = Dice.roll("0d6e6")
        self.assertTotalAndDescription(result, 0, "0 = 0 (0d6e6)")

    def test_zero_fudge_dice(self):
        """Test zero fudge dice."""
        result = Dice.roll("0dF")
        self.assertTotalAndDescription(result, 0, "0 = 0 (0dF)")
