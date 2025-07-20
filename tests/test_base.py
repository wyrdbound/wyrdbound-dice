import sys
import unittest
from pathlib import Path
from unittest import mock

# Add the src directory to the path so we can import wyrdbound_dice
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestDiceBase(unittest.TestCase):
    """Base test class for dice tests with common setup and utilities."""

    def setUp(self):
        self.patcher = mock.patch("random.randint")
        self.mock_randint = self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def assertTotalAndDescription(self, result, expected_total, expected_description):
        self.assertEqual(result.total, expected_total)
        self.assertEqual(str(result), expected_description)
