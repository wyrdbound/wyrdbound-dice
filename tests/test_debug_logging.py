import logging
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

# Add the src directory to the path so we can import wyrdbound_dice
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wyrdbound_dice import Dice
from wyrdbound_dice.debug_logger import StringLogger


class TestDebugLogging(unittest.TestCase):
    def setUp(self):
        self.patcher = mock.patch("random.randint")
        self.mock_randint = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_roll_debug_parameter_exists(self):
        """Test that the roll() method accepts a debug parameter."""
        self.mock_randint.side_effect = [4]
        # This should not raise an error
        result = Dice.roll("1d6", debug=True)
        self.assertEqual(result.total, 4)

    def test_roll_debug_default_false(self):
        """Test that debug defaults to False."""
        self.mock_randint.side_effect = [4]
        # Should work without debug parameter
        result = Dice.roll("1d6")
        self.assertEqual(result.total, 4)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_false_no_output(self, mock_stdout):
        """Test that no debug output is produced when debug=False."""
        self.mock_randint.side_effect = [4]
        result = Dice.roll("1d6", debug=False)
        self.assertEqual(result.total, 4)
        # No debug output should be captured
        output = mock_stdout.getvalue()
        self.assertEqual(output, "")

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_true_produces_output(self, mock_stdout):
        """Test that debug output is produced when debug=True."""
        self.mock_randint.side_effect = [4]
        result = Dice.roll("1d6", debug=True)
        self.assertEqual(result.total, 4)

        # Should have debug output
        output = mock_stdout.getvalue()
        self.assertGreater(len(output), 0)
        self.assertIn("DEBUG", output)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_shows_expression_parsing(self, mock_stdout):
        """Test that debug output shows expression parsing steps."""
        self.mock_randint.side_effect = [3, 4]
        result = Dice.roll("2d6", debug=True)
        self.assertEqual(result.total, 7)

        output = mock_stdout.getvalue()
        # Should show parsing information - either "parsing" or "processing"
        self.assertTrue("parsing" in output.lower() or "processing" in output.lower())
        self.assertIn("2d6", output)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_shows_tokenization(self, mock_stdout):
        """Test that debug output shows tokenization of expressions."""
        self.mock_randint.side_effect = [3, 4, 5]
        result = Dice.roll("2d6 + 5", debug=True)
        self.assertEqual(result.total, 12)

        output = mock_stdout.getvalue()
        # Should show tokenization information
        self.assertIn("token", output.lower())

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_shows_dice_rolling(self, mock_stdout):
        """Test that debug output shows individual dice rolls."""
        self.mock_randint.side_effect = [3, 4]
        result = Dice.roll("2d6", debug=True)
        self.assertEqual(result.total, 7)

        output = mock_stdout.getvalue()
        # Should show individual roll information
        self.assertIn("roll", output.lower())
        self.assertIn("3", output)
        self.assertIn("4", output)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_shows_result_calculation(self, mock_stdout):
        """Test that debug output shows final result calculation."""
        self.mock_randint.side_effect = [3, 4, 5]
        result = Dice.roll("2d6 + 5", debug=True)
        self.assertEqual(result.total, 12)

        output = mock_stdout.getvalue()
        # Should show result calculation
        self.assertIn("result", output.lower())
        self.assertIn("total", output.lower())

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_complex_expression(self, mock_stdout):
        """Test debug output for complex expressions with multiple operations."""
        self.mock_randint.side_effect = [6, 8, 2, 4]
        Dice.roll("2d6 + 2d8 - 3", debug=True)

        output = mock_stdout.getvalue()
        # Should show all parts of the complex expression
        self.assertIn("2d6", output)
        self.assertIn("2d8", output)
        self.assertIn("+", output)
        self.assertIn("-", output)
        self.assertIn("3", output)

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_with_modifiers(self, mock_stdout):
        """Test debug output when using modifiers."""
        self.mock_randint.side_effect = [4]
        modifiers = {"strength": 3}
        Dice.roll("1d6", modifiers=modifiers, debug=True)

        output = mock_stdout.getvalue()
        # Should show modifier information
        self.assertIn("modifier", output.lower())

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_shorthand_expansion(self, mock_stdout):
        """Test debug output shows shorthand expansion."""
        self.mock_randint.side_effect = [1, 2, 3, 4]  # For 4dF
        Dice.roll("FUDGE", debug=True)

        output = mock_stdout.getvalue()
        # Should show shorthand expansion
        self.assertIn("FUDGE", output)
        self.assertIn("4dF", output)
        self.assertIn("shorthand", output.lower())

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_keep_operations(self, mock_stdout):
        """Test debug output for keep operations."""
        self.mock_randint.side_effect = [1, 6, 3]
        Dice.roll("3d6kh1", debug=True)

        output = mock_stdout.getvalue()
        # Should show keep operation information
        self.assertIn("keep", output.lower())
        # Check for either 'h' (parsed format) or 'high'
        self.assertTrue("'h'" in output or "high" in output.lower())

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_precedence_parsing(self, mock_stdout):
        """Test debug output shows precedence parsing decisions."""
        self.mock_randint.side_effect = [3, 4]
        Dice.roll("2d6 * 2 + 5", debug=True)

        output = mock_stdout.getvalue()
        # Should show precedence information
        self.assertIn("precedence", output.lower())

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_debug_error_handling(self, mock_stdout):
        """Test debug output during error conditions."""
        with self.assertRaises(Exception):
            Dice.roll("invalid_expression", debug=True)

        output = mock_stdout.getvalue()
        # Should show debug information even when errors occur
        self.assertGreater(len(output), 0)

    def test_string_logger_injection(self):
        """Test injecting a StringLogger to capture debug output."""
        self.mock_randint.side_effect = [4]
        string_logger = StringLogger()

        result = Dice.roll("1d6", debug=True, logger=string_logger)
        self.assertEqual(result.total, 4)

        # Check that debug output was captured in the string logger
        debug_output = string_logger.get_logs()
        self.assertGreater(len(debug_output), 0)
        self.assertIn("DEBUG", debug_output)
        self.assertIn("Rolling expression", debug_output)
        self.assertIn("1d6", debug_output)

    def test_string_logger_multiple_rolls(self):
        """Test StringLogger with multiple rolls."""
        self.mock_randint.side_effect = [3, 5]
        string_logger = StringLogger()

        # First roll
        result1 = Dice.roll("1d6", debug=True, logger=string_logger)
        self.assertEqual(result1.total, 3)

        # Second roll (should append to existing logs)
        result2 = Dice.roll("1d6", debug=True, logger=string_logger)
        self.assertEqual(result2.total, 5)

        debug_output = string_logger.get_logs()
        # Should contain debug info from both rolls
        self.assertEqual(debug_output.count("Rolling expression"), 2)
        self.assertIn("Rolling 1d6: 3", debug_output)
        self.assertIn("Rolling 1d6: 5", debug_output)

    def test_string_logger_clear(self):
        """Test clearing the StringLogger."""
        self.mock_randint.side_effect = [4]
        string_logger = StringLogger()

        result = Dice.roll("1d6", debug=True, logger=string_logger)
        self.assertEqual(result.total, 4)

        # Verify we have debug output
        debug_output = string_logger.get_logs()
        self.assertGreater(len(debug_output), 0)

        # Clear and verify it's empty
        string_logger.clear()
        debug_output = string_logger.get_logs()
        self.assertEqual(len(debug_output), 0)

    def test_python_logger_injection(self):
        """Test injecting a standard Python logger."""
        self.mock_randint.side_effect = [6]

        # Create a custom logger with a StringIO handler
        logger = logging.getLogger("test_logger")
        logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        logger.handlers.clear()

        # Add a StringIO handler to capture output
        string_stream = StringIO()
        handler = logging.StreamHandler(string_stream)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)

        result = Dice.roll("1d6", debug=True, logger=logger)
        self.assertEqual(result.total, 6)

        # Check that our custom logger received the messages
        output = string_stream.getvalue()
        self.assertGreater(len(output), 0)
        self.assertIn("DEBUG:", output)
        self.assertIn("Rolling expression", output)

    def test_custom_logger_protocol(self):
        """Test using a custom logger that implements the logging interface."""
        self.mock_randint.side_effect = [6]

        class CustomLogger:
            def __init__(self):
                self.messages = []

            def debug(self, message):
                self.messages.append(f"CUSTOM: {message}")

            def info(self, message):
                self.messages.append(f"CUSTOM: {message}")

            def warning(self, message):
                self.messages.append(f"CUSTOM: {message}")

            def error(self, message):
                self.messages.append(f"CUSTOM: {message}")

        custom_logger = CustomLogger()
        result = Dice.roll("1d6", debug=True, logger=custom_logger)
        self.assertEqual(result.total, 6)

        # Check that our custom logger received the messages
        self.assertGreater(len(custom_logger.messages), 0)
        self.assertTrue(any("CUSTOM: DEBUG:" in msg for msg in custom_logger.messages))

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_default_stdout_logger_still_works(self, mock_stdout):
        """Test that default stdout logging still works when no custom logger is provided."""
        self.mock_randint.side_effect = [4]
        result = Dice.roll("1d6", debug=True)  # No custom logger
        self.assertEqual(result.total, 4)

        output = mock_stdout.getvalue()
        self.assertGreater(len(output), 0)
        self.assertIn("DEBUG", output)


if __name__ == "__main__":
    unittest.main()
