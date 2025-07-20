from test_base import TestDiceBase

from wyrdbound_dice import Dice, DivisionByZeroError, ParseError


class TestDiceWithChaosEngineering(TestDiceBase):
    """Chaos engineering tests that explore edge cases and potential failure modes."""

    def test_division_by_zero_handling(self):
        """Test that division by zero consistently raises DivisionByZeroError."""
        # Pure static division by zero should raise DivisionByZeroError
        with self.assertRaises(DivisionByZeroError) as cm:
            Dice.roll("10 / 0")
        self.assertEqual(str(cm.exception), "Division by zero")

        # Dice division by zero should also raise DivisionByZeroError
        self.mock_randint.side_effect = [4]
        with self.assertRaises(DivisionByZeroError) as cm:
            Dice.roll("1d6 / 0")
        self.assertEqual(str(cm.exception), "Division by zero")

        # Zero divided by zero should also raise DivisionByZeroError
        with self.assertRaises(DivisionByZeroError) as cm:
            Dice.roll("0 / 0")
        self.assertEqual(str(cm.exception), "Division by zero")

    def test_zero_sided_die_handling(self):
        """Test edge case of zero-sided dice - now caught by input validation."""
        # 1d0 should now be caught by input validation and raise ParseError
        with self.assertRaises(ParseError) as cm:
            Dice.roll("1d0")
        # The error should mention zero-sided dice
        self.assertIn("zero-sided dice not allowed", str(cm.exception).lower())

    def test_malformed_expression_handling(self):
        """Test that malformed expressions raise ParseError (improved behavior)."""
        # Malformed expressions should raise ParseError instead of returning 0
        malformed_expressions = [
            "",  # Empty string
            "   ",  # Whitespace only
            "d6",  # Missing dice count
            "1d",  # Missing sides
            "invalid",  # Non-dice text
            "1d6+",  # Trailing operator
            "1d6++",  # Double operators
            "1d6*",  # Trailing multiplication
            "+1d6",  # Leading operator without operand
            "1d6 +",  # Trailing operator with space
            "1d-6",  # Negative die sides
        ]

        for expr in malformed_expressions:
            with self.subTest(expr=repr(expr)):
                # All malformed expressions should raise ParseError
                with self.assertRaises(
                    ParseError, msg=f"Expression {repr(expr)} should raise ParseError"
                ):
                    Dice.roll(expr)

    def test_extreme_values_handling(self):
        """Test handling of extremely large values."""
        # Test very large dice count
        self.mock_randint.side_effect = [3] * 1000  # Mock 1000 dice rolls
        r = Dice.roll("1000d6")
        self.assertEqual(r.total, 3000)

        # Test very large die size
        self.mock_randint.side_effect = [500000]
        r = Dice.roll("1d1000000")
        self.assertEqual(r.total, 500000)

        # Test very large multiplier
        self.mock_randint.side_effect = [6]
        r = Dice.roll("1d6 x 1000000")
        self.assertEqual(r.total, 6000000)

    def test_decimal_inputs_handling(self):
        """Test how decimal inputs are handled - some behaviors might be bugs."""
        # Test decimal dice count - what does 1.5d6 even mean?
        # This should raise a ParseError because 1.5 dice doesn't make sense (parsing issue)
        with self.assertRaises(ParseError, msg="1.5d6 should raise ParseError"):
            Dice.roll("1.5d6")

        # Test decimal sides - what does 1d6.5 mean?
        # This should raise a ParseError because 6.5-sided die doesn't make sense (parsing issue)
        with self.assertRaises(ParseError, msg="1d6.5 should raise ParseError"):
            Dice.roll("1d6.5")

        # These expressions currently work due to string parsing quirks rather than intentional design

    def test_keep_operations_edge_cases(self):
        """Test edge cases in keep operations that should fail."""
        # Test keeping zero dice - this should probably return 0, not sum of all dice
        self.mock_randint.side_effect = [1, 2, 3, 4]
        r = Dice.roll("4d6kh0")
        # ACTUAL BUG: Keeping 0 dice returns sum of all dice instead of 0
        # This assertion will FAIL, showing the bug exists
        self.assertTotalAndDescription(r, 0, "0 = 0 (4d6kh0: 1, 2, 3, 4)")

        # Test keeping more dice than available (highest)
        self.mock_randint.side_effect = [1, 2, 3, 4]
        r = Dice.roll("4d6kh10")
        # This behavior seems reasonable - return all dice if asking for more than available
        self.assertTotalAndDescription(r, 10, "10 = 10 (4d6kh10: 1, 2, 3, 4)")

        # Test expression that looks like negative keep but is actually valid subtraction
        self.mock_randint.side_effect = [1, 2]
        # The new parser correctly interprets "2d6kh-1" as "(2d6kh) - 1" which is valid
        r = Dice.roll("2d6kh-1")
        # Should be (2 - 1) = 1 since kh without number means kh1, keeping highest roll
        self.assertTotalAndDescription(r, 1, "1 = 2 (2d6kh1: 1, 2) - 1")

        # Test keep lowest zero - this correctly returns 0
        self.mock_randint.side_effect = [1, 2, 3, 4]
        r = Dice.roll("4d6kl0")
        self.assertTotalAndDescription(r, 0, "0 = 0 (4d6kl0: 1, 2, 3, 4)")

        # Test keeping more dice than available (lowest)
        self.mock_randint.side_effect = [1, 2, 3, 4]
        r = Dice.roll("4d6kl10")
        # This behavior seems reasonable - return all dice if asking for more than available
        self.assertTotalAndDescription(r, 10, "10 = 10 (4d6kl10: 1, 2, 3, 4)")

    def test_complex_expression_evaluation_order(self):
        """Test that complex expressions evaluate in correct order."""
        # Test mathematical precedence edge cases
        test_cases = [
            ("2 + 3 x 4", 14),  # Should be 2 + (3 x 4) = 14
            ("10 - 2 x 3", 4),  # Should be 10 - (2 x 3) = 4
            ("12 / 3 x 2", 8),  # Should be (12 / 3) x 2 = 8
            ("1 + 2 x 3 + 4", 11),  # Should be 1 + (2 x 3) + 4 = 11
            ("20 / 4 / 2", 2),  # Should be (20 / 4) / 2 = 2
        ]

        for expr, expected in test_cases:
            with self.subTest(expr=expr):
                result = Dice.roll(expr)
                self.assertEqual(
                    result.total, expected, f"Expression {expr} evaluated incorrectly"
                )

    def test_double_keep_handling(self):
        """Test expressions with multiple keep operations."""
        # These currently work but behavior might be unexpected/undefined

        # Test double keep - kh1kl1 means keep highest 1 then keep lowest 1 of that
        self.mock_randint.side_effect = [1, 2, 3, 4, 5]
        result = Dice.roll("5d6kh2kl1")  # Keep highest 2, then lowest 1 of those 2
        self.assertTotalAndDescription(result, 4, "4 = 4 (5d6kh2kl1: 1, 2, 3, 4, 5)")

        # Test double keep with different keep types
        self.mock_randint.side_effect = [1, 2, 3, 4, 5]
        result = Dice.roll("5d6kl2kh1")  # Keep lowest 2, then highest 1 of those 2
        self.assertTotalAndDescription(result, 2, "2 = 2 (5d6kl2kh1: 1, 2, 3, 4, 5)")

        # Test double keep with different die size
        self.mock_randint.side_effect = [10, 4, 19]
        result = Dice.roll("3d20kl2kh1")  # Keep lowest 2, then highest 1 of those 2
        self.assertTotalAndDescription(result, 10, "10 = 10 (3d20kl2kh1: 10, 4, 19)")

        # Test double keep with same keep types
        self.mock_randint.side_effect = [1, 2, 3, 4, 5]
        result = Dice.roll("5d6kh2kh1")  # Same as 5d6kh1
        self.assertTotalAndDescription(result, 5, "5 = 5 (5d6kh2kh1: 1, 2, 3, 4, 5)")

    def test_double_explode_handling(self):
        # Test double explode - does e6e4 mean explode on 6 AND explode on 4?
        self.mock_randint.side_effect = [4, 6, 2]  # 4 explodes, 6 explodes, 2 stops
        # BUG?: Double explode semantics are unclear - could cause infinite loops
        with self.assertRaises(
            ParseError, msg="Expression 1d6e6e4 should raise ParseError"
        ) as cm:
            Dice.roll("1d6e6e4")
        # The error should mention multiple explode conditions not allowed
        self.assertIn(
            "multiple explode conditions not allowed", str(cm.exception).lower()
        )

    def test_fudge_dice_with_zero_dice(self):
        """Test fudge dice rolling no dice."""
        r = Dice.roll("0dF")
        self.assertTotalAndDescription(r, 0, "0 = 0 (0dF)")

    def test_fudge_dice_with_keep_highest(self):
        """Test fudge dice combined with keep highest."""
        self.mock_randint.side_effect = [1, 5]
        r = Dice.roll("2dFkh1")
        self.assertTotalAndDescription(r, 1, "1 = 1 (2dFkh1: -, +)")

    def test_fudge_dice_with_keep_highest_zero_rolls(self):
        """Test fudge dice combined with keep highest zero rolls."""
        self.mock_randint.side_effect = [1, 2, 3, 4]
        r = Dice.roll("4dFkh0")
        self.assertTotalAndDescription(r, 0, "0 = 0 (4dFkh0: -, -, B, B)")

    def test_fudge_dice_with_keep_lowest(self):
        """Test fudge dice combined with keep lowest."""
        self.mock_randint.side_effect = [
            1,
            2,
            3,
            4,
            5,
            6,
            4,
            2,
        ]  # Fudge values: -, -, B, B, +, +, B, -
        r = Dice.roll("8dFkl4")
        self.assertTotalAndDescription(
            r, -3, "-3 = -3 (8dFkl4: -, -, B, B, +, +, B, -)"
        )

    def test_fudge_dice_with_keep_lowest_zero_rolls(self):
        """Test fudge dice combined with keep lowest zero rolls."""
        self.mock_randint.side_effect = [1, 2, 3, 4]
        r = Dice.roll("4dFkl0")
        self.assertTotalAndDescription(r, 0, "0 = 0 (4dFkl0: -, -, B, B)")

    def test_fudge_dice_with_reroll_force_positive(self):
        """Test fudge dice combined with reroll."""
        self.mock_randint.side_effect = [1, 2, 3, 4, 5, 6, 4, 2]
        with self.assertRaises(ParseError) as cm:
            # This should raise an error because reroll is not supported for fudge dice
            Dice.roll("4dFr<=0")  # Reroll if <= 0
        self.assertEqual(cm.exception.condition_type, "reroll")
        self.assertIn(
            "reroll is not supported for fudge dice", str(cm.exception).lower()
        )

    def test_fudge_dice_with_multiplication(self):
        """Test fudge dice combined with other modifiers."""
        self.mock_randint.side_effect = [1]  # Fudge values: -, -, B, B
        r = Dice.roll("1dFx2")
        self.assertTotalAndDescription(r, -2, "-2 = -1 (1dF: -) x 2")

    def test_extreme_dice_expressions_extreme_modifier(self):
        """Test extreme dice expressions with extreme modifiers."""
        self.mock_randint.side_effect = [10, 500]
        mods = {"extreme_mod": "1d1000"}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r, 510, "510 = 10 (1d20: 10) + 500 (extreme_mod: 500 = 500 (1d1000: 500))"
        )

    def test_extreme_dice_expressions_extreme_negative_modifier(self):
        """Test extreme dice expressions with extreme negative modifiers."""
        self.mock_randint.side_effect = [10, 500]
        mods = {"negative_mod": "-1d1000"}
        r = Dice.roll("1d20", modifiers=mods)
        self.assertTotalAndDescription(
            r,
            -490,
            "-490 = 10 (1d20: 10) - 500 (negative_mod: 500 = 500 (1d1000: 500))",
        )

    def test_thread_safety_for_concurrent_rolling(self):
        """Test that concurrent dice rolling doesn't cause issues."""

        import threading

        results = []
        errors = []

        def roll_dice():
            try:
                for _ in range(5):  # Reduced iterations for faster testing
                    result = Dice.roll("2d6+5")
                    results.append(result.total)
            except Exception as e:
                errors.append(e)

        # Disable mocking for this test since we want real random behavior
        self.patcher.stop()
        try:
            # Run multiple threads
            threads = []
            for _ in range(3):
                t = threading.Thread(target=roll_dice)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # Should have no errors and reasonable results
            self.assertEqual(
                len(errors), 0, f"Concurrent rolling caused errors: {errors}"
            )
            self.assertEqual(len(results), 15)  # 3 threads × 5 rolls each
            self.assertTrue(
                all(7 <= r <= 17 for r in results),
                f"Some results outside expected range: {results}",
            )
        finally:
            # Restart mocking for other tests
            self.patcher.start()

    def test_division_by_zero(self):
        """Test that division by zero consistently raises DivisionByZeroError."""
        test_cases = [
            "1d6 / 0",  # Division by zero should raise DivisionByZeroError
            "1d6 x 1d6 / 0",  # Complex expression with division by zero
            "2d8 + 3 / 0",  # Mixed expression with division by zero
        ]

        for expr in test_cases:
            with self.subTest(expr=expr):
                # Division by zero should raise DivisionByZeroError consistently
                with self.assertRaises(DivisionByZeroError):
                    Dice.roll(expr)

    def test_roll_ranges(self):
        """Test statistical ranges of dice rolls to ensure no unexpected results or behavior."""
        # Test cases below are die and the statistical ranges they should produce
        test_cases = [
            ["1d4", (1, 4)],
            ["1d6", (1, 6)],
            ["1d8", (1, 8)],
            ["1d10", (1, 10)],
            ["1d12", (1, 12)],
            ["1d20", (1, 20)],
            ["1d100", (1, 100)],
        ]

        # Stop mocking randint to allow real random rolls
        self.patcher.stop()

        for expr, expected_range in test_cases:
            with self.subTest(expr=expr):
                for _ in range(100):
                    # Perform actual rolls to test statistical validity
                    result = Dice.roll(expr)
                    self.assertIsInstance(
                        result.total, int, f"Result for {expr} should be an integer"
                    )
                    # Check if the result is within the desired range
                    self.assertGreaterEqual(
                        result.total,
                        expected_range[0],
                        f"Result {result.total} for {expr} is less than {expected_range[0]}",
                    )
                    self.assertLessEqual(
                        result.total,
                        expected_range[1],
                        f"Result {result.total} for {expr} exceeds maximum {expected_range[1]}",
                    )

        # Restart mocking for other tests
        self.patcher.start()

    def test_complex_operations_dice_with_modifiers(self):
        """Test complex operations with dice and modifiers."""
        self.mock_randint.side_effect = [4, 6, 2, 2, 3, 1, 17]
        result = Dice.roll("1d6 + 2d8 - 3d4 + 1d20 - 5")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(
            result,
            18,
            "18 = 4 (1d6: 4) + 8 (2d8: 6, 2) - 6 (3d4: 2, 3, 1) + 17 (1d20: 17) - 5",
        )

    def test_complex_operations_multiple_multiplications(self):
        """Test complex operations with multiple multiplications."""
        self.mock_randint.side_effect = [6, 8, 4]
        result = Dice.roll("1d6 x 2 + 1d8 x 3 - 1d4 x 4")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(
            result, 20, "20 = 6 (1d6: 6) x 2 + 8 (1d8: 8) x 3 - 4 (1d4: 4) x 4"
        )

    def test_complex_operations_multiple_divisions(self):
        """Test complex operations with multiple divisions."""
        self.mock_randint.side_effect = [10, 4, 8]
        result = Dice.roll("1d20 / 2 + 1d12 / 3 - 1d8 / 4")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(
            result, 4, "4 = 10 (1d20: 10) / 2 + 4 (1d12: 4) / 3 - 8 (1d8: 8) / 4"
        )

    def test_complex_operations_multiple_keeps(self):
        """Test complex operations with multiple keep operations."""
        self.mock_randint.side_effect = [6, 3, 4, 7, 2, 3, 4, 2, 1]
        result = Dice.roll("2d6kh1 + 3d8kl2 - 4d4kh3")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(
            result,
            3,
            "3 = 6 (2d6kh1: 6, 3) + 6 (3d8kl2: 4, 7, 2) - 9 (4d4kh3: 3, 4, 2, 1)",
        )

    def test_complex_operations_with_special_modifiers(self):
        self.mock_randint.side_effect = [2, 6, 7, 3, 1, 1]
        result = Dice.roll("1d6r<=2 + 1d8e>=7 - 1d4r1<2")
        self.assertIsInstance(result.total, int)
        self.assertTotalAndDescription(
            result,
            15,
            "15 = 6 (1d6r<=2: 2, 6) + 10 (1d8e>=7: 7, 3) - 1 (1d4r1<2: 1, 1)",
        )

    def test_modifier_edge_cases_with_dice(self):
        """Test edge cases with dice modifiers."""
        # Test modifiers with extreme or unusual dice expressions
        test_cases = [
            ("1d6", {"zero_dice": "0d6"}, 1),  # Zero dice modifier
            ("1d6", {"self_ref": "1d6"}, 2),  # Same die type in modifier
            ("1d20", {"huge_dice": "1d1000"}, 2),  # Very large die in modifier
            ("1d6", {"many_dice": "100d1"}, 101),  # Many dice in modifier
            ("1d6", {"fudge_mod": "4dF"}, -3),  # Fudge dice modifier
            ("1d6", {"negative_huge": "-1d100"}, 0),  # Large negative modifier
        ]

        for base_expr, mods, expected in test_cases:
            with self.subTest(base_expr=base_expr, mods=mods):
                # Provide enough mock values for complex modifiers
                self.mock_randint.side_effect = [1] * 200  # Enough for 100d1 + extra
                result = Dice.roll(base_expr, modifiers=mods)
                self.assertIsInstance(result.total, int)
                self.assertEqual(
                    result.total,
                    expected,
                    f"Expression {base_expr} with modifiers {mods} should return {expected}",
                )

    def test_expression_length_limits(self):
        """Test very long expressions that might stress parsing."""
        # Create a very long expression with many terms
        long_expr = "1d6"
        for i in range(20):  # Add 20 more terms
            long_expr += f" + 1d{6 + (i % 6)}"  # Vary die types

        # Provide enough mock values for the long expression
        self.mock_randint.side_effect = [3] * 30
        result = Dice.roll(long_expr)
        self.assertIsInstance(result.total, int)

        # Should be sum of all dice (21 dice rolling 3 each = 63)
        self.assertTotalAndDescription(
            result,
            63,
            "63 = 3 (1d6: 3) + 3 (1d6: 3) + 3 (1d7: 3) + 3 (1d8: 3) + 3 (1d9: 3) + 3 (1d10: 3) + 3 (1d11: 3) + 3 (1d6: 3) + 3 (1d7: 3) + 3 (1d8: 3) + 3 (1d9: 3) + 3 (1d10: 3) + 3 (1d11: 3) + 3 (1d6: 3) + 3 (1d7: 3) + 3 (1d8: 3) + 3 (1d9: 3) + 3 (1d10: 3) + 3 (1d11: 3) + 3 (1d6: 3) + 3 (1d7: 3)",
        )

    def test_keep_operations_with_zero_and_negative(self):
        """Test keep operations with zero and negative values."""

        # Test keeping zero highest
        self.mock_randint.side_effect = [3] * 5
        result = Dice.roll("5d6kh0")
        # This now works correctly - kh0 keeps 0 dice and returns total=0
        self.assertTotalAndDescription(result, 0, "0 = 0 (5d6kh0: 3, 3, 3, 3, 3)")

        # Test keeping zero lowest
        self.mock_randint.side_effect = [3] * 5
        result = Dice.roll("5d6kl0")
        self.assertTotalAndDescription(result, 0, "0 = 0 (5d6kl0: 3, 3, 3, 3, 3)")

        # Test expression that looks like negative keep but is actually subtraction
        self.mock_randint.side_effect = [3] * 5
        result = Dice.roll("5d6kh-1")
        # The new parser interprets this as "(5d6kh) - 1" which is valid
        self.assertTotalAndDescription(result, 2, "2 = 3 (5d6kh1: 3, 3, 3, 3, 3) - 1")

    def test_negative_dice_roll(self):
        """Test negative dice count - should return 0 minus the roll's result."""
        # Negative dice should return 0 minus the roll
        self.mock_randint.side_effect = [3, 4, 5]
        result = Dice.roll("-1d6")
        self.assertTotalAndDescription(result, -3, "-3 = 0 - 3 (1d6: 3)")

    def test_negative_dice_with_modifiers(self):
        self.mock_randint.side_effect = [3, 4]
        result = Dice.roll("-2d6 + 5")
        self.assertTotalAndDescription(result, -2, "-2 = 0 - 7 (2d6: 3, 4) + 5")

    def test_negative_dice_with_keep_operations(self):
        self.mock_randint.side_effect = [3, 4, 5]
        result = Dice.roll("-3d6kh1")
        self.assertTotalAndDescription(result, -5, "-5 = 0 - 5 (3d6kh1: 3, 4, 5)")

    def test_negative_dice_with_reroll(self):
        self.mock_randint.side_effect = [2, 4, 5]
        result = Dice.roll("-1d6r<=2")  # Reroll if <= 2
        self.assertTotalAndDescription(result, -4, "-4 = 0 - 4 (1d6r<=2: 2, 4)")

    def test_negative_dice_with_explosion(self):
        self.mock_randint.side_effect = [3, 6, 2]
        result = Dice.roll("-2d6e6")  # Explode on 6
        self.assertTotalAndDescription(result, -11, "-11 = 0 - 11 (2d6e6: 3, 6, 2)")

    def test_negative_dice_with_fudge_dice(self):
        self.mock_randint.side_effect = [1, 2, 3, 4]
        result = Dice.roll("-4dF")  # Fudge dice
        self.assertTotalAndDescription(result, 2, "2 = 0 + 2 (4dF: -, -, B, B)")

    def test_negative_dice_with_roll_modifiers(self):
        self.mock_randint.side_effect = [3, 4, 5]
        mods = {"positive_mod": "1d6"}
        result = Dice.roll("-1d6", modifiers=mods)
        self.assertTotalAndDescription(
            result, 1, "1 = 0 - 3 (1d6: 3) + 4 (positive_mod: 4 = 4 (1d6: 4))"
        )

    def test_negative_dice_complex_expressions(self):
        self.mock_randint.side_effect = [3, 4, 5]
        result = Dice.roll("-1d6 + 2d6")
        self.assertTotalAndDescription(result, 6, "6 = 0 - 3 (1d6: 3) + 9 (2d6: 4, 5)")
