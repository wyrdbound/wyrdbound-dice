#!/usr/bin/env python3
"""
Roll dice from the command line using wyrdbound-dice.

Examples:
  roll.py "1d20"                 # Simple d20 roll
  roll.py "2d6 + 3"              # Two d6 plus 3
  roll.py "2d20kh1"              # Advantage (keep highest)
  roll.py "1d20" --json          # Output as JSON
  roll.py "1d6" -n 5 --json      # Multiple rolls as JSON array
  roll.py "2d6 + 3" --debug      # Show debug logging
  roll.py "1d20" --seed 42       # Reproducible roll
  roll.py "1d6" -n 3 --seed 42   # Reproducible batch
"""

import argparse
import json
import random
import sys
from pathlib import Path

# Add the src directory to the path so we can import wyrdbound_dice
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wyrdbound_dice import Dice, DivisionByZeroError, InfiniteConditionError, ParseError
from wyrdbound_dice.debug_logger import StringLogger

parser = argparse.ArgumentParser(
    description="Roll dice expressions using WyrdBound Dice"
)

parser.add_argument("expression", help="Dice expression to roll")
parser.add_argument(
    "-v", "--verbose", action="store_true", help="Show detailed breakdown"
)
parser.add_argument("-n", "--count", type=int, default=1, help="Number of rolls")
parser.add_argument("--json", action="store_true", help="Output results as JSON")
parser.add_argument(
    "--debug",
    action="store_true",
    help="Enable debug logging to see detailed parsing and rolling steps",
)
parser.add_argument(
    "--seed",
    type=int,
    default=None,
    metavar="N",
    help="Integer seed for reproducible rolls (e.g. --seed 42)",
)

args = parser.parse_args()

# Build rng from seed if provided; a fresh Random(seed) is used per-run so
# --count N with --seed produces a deterministic sequence across all N rolls.
rng = random.Random(args.seed) if args.seed is not None else None

try:
    results = []

    for i in range(args.count):
        # For JSON output with debug, use StringLogger to capture debug info
        if args.json and args.debug:
            string_logger = StringLogger()
            result = Dice.roll(
                args.expression, debug=args.debug, logger=string_logger, rng=rng
            )
            debug_output = string_logger.get_logs()
        else:
            result = Dice.roll(args.expression, debug=args.debug, rng=rng)
            debug_output = None

        if args.json:
            # Collect results for JSON output
            roll_data = {"result": result.total, "description": str(result)}
            if debug_output:
                roll_data["debug"] = debug_output
            results.append(roll_data)
        else:
            # Regular text output
            if args.count > 1:
                print(f"\n--- Roll {i + 1} ---")
            print(result)

    # Output JSON if requested
    if args.json:
        if args.count == 1:
            # Single roll: return object, include seed if provided
            output = results[0]
            if args.seed is not None:
                output["seed"] = args.seed
            print(json.dumps(output, indent=2))
        else:
            # Multiple rolls: wrap in object with seed when provided
            if args.seed is not None:
                print(json.dumps({"seed": args.seed, "results": results}, indent=2))
            else:
                print(json.dumps(results, indent=2))

    exit(0)

except (ParseError, DivisionByZeroError, InfiniteConditionError) as e:
    print(f"Dice Error: {e}", file=sys.stderr)
    exit(1)
except Exception as e:
    print(f"Unexpected error: {e}", file=sys.stderr)
    exit(1)
