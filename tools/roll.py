#!/usr/bin/env python3
"""
Roll dice from the command line using wyrdbound-dice.

Examples:
  roll.py "1d20"                 # Simple d20 roll
  roll.py "2d6 + 3"              # Two d6 plus 3
  roll.py "2d20kh1"              # Advantage (keep highest)
  roll.py "1d20" --json          # Output as JSON
  roll.py "1d6" -n 5 --json      # Multiple rolls as JSON array
"""

import argparse
import json
import sys
from pathlib import Path

# Add the src directory to the path so we can import wyrdbound_dice
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wyrdbound_dice import Dice, DivisionByZeroError, InfiniteConditionError, ParseError

parser = argparse.ArgumentParser(
    description="Roll dice expressions using WyrdBound Dice"
)

parser.add_argument("expression", help="Dice expression to roll")
parser.add_argument(
    "-v", "--verbose", action="store_true", help="Show detailed breakdown"
)
parser.add_argument("-n", "--count", type=int, default=1, help="Number of rolls")
parser.add_argument("--json", action="store_true", help="Output results as JSON")

args = parser.parse_args()

try:
    results = []

    for i in range(args.count):
        result = Dice.roll(args.expression)

        if args.json:
            # Collect results for JSON output
            roll_data = {"result": result.total, "description": str(result)}
            results.append(roll_data)
        else:
            # Regular text output
            if args.count > 1:
                print(f"\n--- Roll {i + 1} ---")
            print(result)

    # Output JSON if requested
    if args.json:
        if args.count == 1:
            # Single roll: return just the object
            print(json.dumps(results[0], indent=2))
        else:
            # Multiple rolls: return array
            print(json.dumps(results, indent=2))

    exit(0)

except (ParseError, DivisionByZeroError, InfiniteConditionError) as e:
    print(f"Dice Error: {e}", file=sys.stderr)
    exit(1)
except Exception as e:
    print(f"Unexpected error: {e}", file=sys.stderr)
    exit(1)
