"""Test the convenience roll function that was added to fix the CI issue."""

from wyrdbound_dice import Dice, StringLogger, roll


def test_roll_convenience_function_basic():
    """Test that the convenience roll function works for basic dice expressions."""
    result = roll("2d6+3")
    assert 5 <= result.total <= 15
    assert str(result)  # Should have string representation


def test_roll_convenience_function_with_modifiers():
    """Test the roll function with modifiers parameter."""
    result = roll("1d6", modifiers={"bonus": 2})
    assert 3 <= result.total <= 8  # 1-6 + 2


def test_roll_convenience_function_with_debug_logger():
    """Test the roll function with debug logger."""
    logger = StringLogger()
    result = roll("1d6", debug=True, debug_logger=logger)

    assert 1 <= result.total <= 6
    assert logger.get_logs()  # Should have debug content


def test_roll_function_equivalent_to_dice_roll():
    """
    Test that the convenience function produces the same type of
    result as Dice.roll().
    """
    # They won't have same values due to randomness,
    # but should have same structure
    dice_result = Dice.roll("1d20")
    func_result = roll("1d20")

    assert isinstance(dice_result, type(func_result))
    assert hasattr(dice_result, "total")
    assert hasattr(func_result, "total")
    assert hasattr(dice_result, "results")
    assert hasattr(func_result, "results")


def test_ci_specific_test_case():
    """Test the exact scenario that was failing in CI."""
    from wyrdbound_dice import roll

    result = roll("2d6+3")
    print(f"Test roll result: {result.total}")
    assert 5 <= result.total <= 15
    print("✓ Basic functionality test passed")
