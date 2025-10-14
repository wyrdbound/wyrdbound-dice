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

    def test_roll_reroll_with_keep_after(self):
        """Test reroll followed by keep operation (4d6r<=2kh3)."""
        # Roll 4d6, reroll any <=2, then keep highest 3
        self.mock_randint.side_effect = [
            1,
            3,
            2,
            5,
            4,
            6,
        ]  # First: 1, 3, 2, 5 -> reroll 1, 2 -> 4, 6
        r = Dice.roll("4d6r<=2kh3")
        # Final rolls after reroll: [3, 5, 4, 6], keep highest 3: [4, 5, 6] = 15
        self.assertEqual(r.total, 15)
        self.assertEqual(len(r.results[0].kept), 3)
        self.assertEqual(sorted(r.results[0].kept), [4, 5, 6])

    def test_roll_reroll_with_keep_before(self):
        """Test keep followed by reroll operation (4d6kh3r<=2)."""
        # Roll 4d6, keep highest 3, then reroll any <=2 in those kept
        self.mock_randint.side_effect = [
            1,
            3,
            2,
            5,
            4,
            6,
        ]  # First: 1, 3, 2, 5 -> reroll 1, 2 -> 4, 6
        r = Dice.roll("4d6kh3r<=2")
        # Should produce the same result as reroll-then-keep
        self.assertEqual(r.total, 15)
        self.assertEqual(len(r.results[0].kept), 3)
        self.assertEqual(sorted(r.results[0].kept), [4, 5, 6])

    def test_roll_reroll_with_keep_lowest_after(self):
        """Test reroll followed by keep lowest operation (4d6r>=5kl2)."""
        # Roll 4d6, reroll any >=5, then keep lowest 2
        self.mock_randint.side_effect = [
            6,
            3,
            5,
            2,
            4,
            1,
        ]  # First: 6, 3, 5, 2 -> reroll 6, 5 -> 4, 1
        r = Dice.roll("4d6r>=5kl2")
        # Final rolls after reroll: [3, 2, 4, 1], keep lowest 2: [1, 2] = 3
        self.assertEqual(r.total, 3)
        self.assertEqual(len(r.results[0].kept), 2)
        self.assertEqual(sorted(r.results[0].kept), [1, 2])

    def test_roll_reroll_with_drop_after(self):
        """Test reroll followed by drop operation (4d6r<=2dh1)."""
        # Roll 4d6, reroll any <=2, then drop highest 1
        self.mock_randint.side_effect = [
            1,
            3,
            2,
            5,
            4,
            6,
        ]  # First: 1, 3, 2, 5 -> reroll 1, 2 -> 4, 6
        r = Dice.roll("4d6r<=2dh1")
        # Final rolls after reroll: [3, 5, 4, 6], drop highest 1 (6): [3, 4, 5] = 12
        self.assertEqual(r.total, 12)
        self.assertEqual(len(r.results[0].kept), 3)
        self.assertEqual(sorted(r.results[0].kept), [3, 4, 5])
