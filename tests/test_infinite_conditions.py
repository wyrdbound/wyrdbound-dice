from test_base import TestDiceBase

from wyrdbound_dice import Dice, InfiniteConditionError


class TestInfiniteConditions(TestDiceBase):
    """Infinite reroll and exploding conditions that create impossible loops."""

    def test_infinite_reroll_conditions_equals_max_sides(self):
        """Reroll conditions that match all possible rolls create infinite loops."""
        # Expression: 1d10r<=10 (reroll if <= 10, but max roll is 10, so always rerolls)
        # This creates an impossible condition - every roll triggers a reroll
        with self.assertRaises(InfiniteConditionError) as cm:
            Dice.roll("1d10r<=10")
        self.assertEqual(cm.exception.condition_type, "reroll")
        self.assertEqual(cm.exception.expression, "1d10r<=10")

    def test_infinite_reroll_pattern_NdMr_equals_M(self):
        """The pattern NdMr<=M should be detected as creating infinite rerolls."""
        # Expression: 2d6r<=6 (reroll if <= 6, but max roll is 6)
        # This is impossible - every roll will trigger a reroll
        with self.assertRaises(InfiniteConditionError) as cm:
            Dice.roll("2d6r<=6")
        self.assertEqual(cm.exception.condition_type, "reroll")
        self.assertEqual(cm.exception.expression, "2d6r<=6")

    def test_infinite_reroll_pattern_various_dice(self):
        """Test the NdMr<=M pattern with different dice types."""
        # Test with d4, d8, d12, d20 - all should fail with the <=max pattern
        test_cases = [
            ("1d4r<=4", "reroll"),
            ("1d8r<=8", "reroll"),
            ("1d12r<=12", "reroll"),
            ("1d20r<=20", "reroll"),
        ]

        for expression, expected_type in test_cases:
            with self.subTest(expression=expression):
                with self.assertRaises(InfiniteConditionError) as cm:
                    Dice.roll(expression)
                self.assertEqual(cm.exception.condition_type, expected_type)
                self.assertEqual(cm.exception.expression, expression)

    def test_infinite_reroll_greater_than_or_equal_to_one(self):
        """Reroll conditions >=1 should create infinite loops since all rolls are >=1."""
        # Expression: 1d6r>=1 (reroll if >= 1, but min roll is 1)
        # This is impossible - every roll will trigger a reroll
        with self.assertRaises(InfiniteConditionError) as cm:
            Dice.roll("1d6r>=1")
        self.assertEqual(cm.exception.condition_type, "reroll")
        self.assertEqual(cm.exception.expression, "1d6r>=1")

    def test_infinite_reroll_equals_conditions(self):
        """Test various = conditions that could create infinite loops."""
        # While 1d6r=6 is fine (only rerolls on 6), testing edge cases
        # 1d1r=1 would be infinite since the only possible roll is 1
        with self.assertRaises(InfiniteConditionError) as cm:
            Dice.roll("1d1r=1")
        self.assertEqual(cm.exception.condition_type, "reroll")
        self.assertEqual(cm.exception.expression, "1d1r=1")

    def test_pathological_exploding_conditions(self):
        """REAL BUG: Exploding conditions that apply to all rolls create infinite explosions.

        This is a real bug - conditions like 1d4e>=1 are logically impossible since
        every roll (1-4) meets the condition >=1, creating infinite explosions.
        """
        # Expression: 1d4e>=1 (explode if >= 1, which is 100% of rolls)
        # This creates an infinite explosion scenario - every roll explodes
        with self.assertRaises(InfiniteConditionError) as cm:
            Dice.roll("1d4e>=1")
        self.assertEqual(cm.exception.condition_type, "explosion")
        self.assertEqual(cm.exception.expression, "1d4e>=1")
