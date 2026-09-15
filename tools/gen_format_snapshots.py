#!/usr/bin/env python3
"""Generate the roll-rendering characterization snapshots.

Renders every entry in ``tests/format_corpus.py`` against the current code and
writes ``tests/data/format_snapshots.json``. The output is the regression
contract for default roll rendering -- regenerate it only after explicit
sign-off, never to make a failing snapshot test go green.
"""

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from format_corpus import EXPRESSIONS, MODIFIER_CASES, SEED  # noqa: E402

from wyrdbound_dice import Dice  # noqa: E402

SNAPSHOT_PATH = REPO_ROOT / "tests" / "data" / "format_snapshots.json"


def render(expression, modifiers=None):
    """Render one corpus entry, pinning exceptions by their class name."""
    try:
        result = Dice.roll(expression, modifiers=modifiers, rng=random.Random(SEED))
    except Exception as exc:  # noqa: BLE001 - snapshots pin the exception type
        return "!" + type(exc).__name__
    return str(result)


def main():
    """Render the corpus and write the snapshot JSON."""
    snapshots = {}

    for expression in EXPRESSIONS:
        snapshots[expression] = render(expression)

    for expression, modifiers in MODIFIER_CASES:
        key = expression + " ||| " + json.dumps(modifiers, sort_keys=True)
        snapshots[key] = render(expression, modifiers)

    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(
        json.dumps(snapshots, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    print("Wrote {} entries to {}".format(len(snapshots), SNAPSHOT_PATH))


if __name__ == "__main__":
    main()
