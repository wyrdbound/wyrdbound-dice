from test_base import TestDiceBase

from wyrdbound_dice import Dice


class TestDiceModifiers(TestDiceBase):
    def test_roll_with_raw_modifiers(self):
        self.mock_randint.side_effect = [12]
        r = Dice.roll("1d20 + 2 + 1")
        self.assertTotalAndDescription(r, 15, "15 = 12 (1d20: 12) + 2 + 1")

    def test_roll_with_described_modifiers(self):
        self.mock_randint.side_effect = [12]
        mods = {"Str Mod": 2, "Prof Bonus": 2, "Weapon Enchantment": 2}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r,
            18,
            "18 = 12 (1d20: 12) + 2 (Str Mod) + 2 (Prof Bonus) + 2 (Weapon Enchantment)",
        )

    def test_roll_with_mixed_modifiers(self):
        self.mock_randint.side_effect = [12]
        mods = {"Str Mod": 1, "Prof Bonus": 2, "Weapon Enchantment": 3}
        r = Dice.roll("1d20 + 2 + 1 + 3", modifiers=mods)
        self.assertTotalAndDescription(
            r,
            24,
            "24 = 12 (1d20: 12) + 2 + 1 + 3 + 1 (Str Mod) + 2 (Prof Bonus) + 3 (Weapon Enchantment)",
        )

    def test_roll_with_modifiers_negative_values(self):
        self.mock_randint.side_effect = [15]
        mods = {"Penalty": -2, "Disadvantage": -1}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r, 12, "12 = 15 (1d20: 15) - 2 (Penalty) - 1 (Disadvantage)"
        )

    def test_roll_with_modifiers_with_same_values(self):
        self.mock_randint.side_effect = [12]
        mods = {"Str Mod": 2, "Prof Bonus": 2, "Weapon Enchantment": 2}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r,
            18,
            "18 = 12 (1d20: 12) + 2 (Str Mod) + 2 (Prof Bonus) + 2 (Weapon Enchantment)",
        )


class TestDiceModifiersWithDiceExpressions(TestDiceBase):
    def test_roll_with_dice_modifier_positive(self):
        self.mock_randint.side_effect = [12, 3]  # 1d20 rolls 12, 1d4 rolls 3
        mods = {"Guidance": "1d4"}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r, 15, "15 = 12 (1d20: 12) + 3 (Guidance: 3 = 3 (1d4: 3))"
        )

    def test_roll_with_dice_modifier_negative(self):
        self.mock_randint.side_effect = [12, 3]  # 1d20 rolls 12, 1d4 rolls 3
        mods = {"Bane": "-1d4"}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r, 9, "9 = 12 (1d20: 12) - 3 (Bane: 3 = 3 (1d4: 3))"
        )

    def test_roll_with_multiple_dice_modifiers(self):
        self.mock_randint.side_effect = [
            8,
            4,
            2,
        ]  # 1d20 rolls 8, first 1d4 rolls 4, second 1d4 rolls 2
        mods = {"Guidance": "1d4", "Bane": "-1d4"}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r,
            10,
            "10 = 8 (1d20: 8) + 4 (Guidance: 4 = 4 (1d4: 4)) - 2 (Bane: 2 = 2 (1d4: 2))",
        )

    def test_roll_with_complex_dice_modifier(self):
        self.mock_randint.side_effect = [
            10,
            6,
            5,
            3,
        ]  # 1d20 rolls 10, 2d6 rolls 6,5 -> keep highest 1 = 6, 1d4 rolls 3
        mods = {"Bless": "2d6kh1", "Hex": "-1d4"}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r,
            13,
            "13 = 10 (1d20: 10) + 6 (Bless: 6 = 6 (2d6kh1: 6, 5)) - 3 (Hex: 3 = 3 (1d4: 3))",
        )

    def test_roll_with_mixed_static_and_dice_modifiers(self):
        self.mock_randint.side_effect = [
            15,
            2,
            4,
        ]  # 1d20 rolls 15, 1d4 rolls 2, 1d4 rolls 4
        mods = {"Str Mod": 3, "Prof Bonus": 2, "Bane": "-1d4", "Guidance": "1d4"}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r,
            22,
            "22 = 15 (1d20: 15) + 3 (Str Mod) + 2 (Prof Bonus) - 2 (Bane: 2 = 2 (1d4: 2)) + 4 (Guidance: 4 = 4 (1d4: 4))",
        )

    def test_roll_with_dice_expression_and_static_modifiers_in_expression(self):
        self.mock_randint.side_effect = [14, 3]  # 1d20 rolls 14, 1d4 rolls 3
        mods = {"Bane": "-1d4"}
        r = Dice.roll("1d20 + 5", modifiers=mods)
        self.assertTotalAndDescription(
            r, 16, "16 = 14 (1d20: 14) + 5 - 3 (Bane: 3 = 3 (1d4: 3))"
        )

    def test_roll_with_dice_modifier_plus_notation(self):
        self.mock_randint.side_effect = [12, 3]  # 1d20 rolls 12, 1d4 rolls 3
        mods = {"Guidance": "+1d4"}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r, 15, "15 = 12 (1d20: 12) + 3 (Guidance: 3 = 3 (1d4: 3))"
        )
