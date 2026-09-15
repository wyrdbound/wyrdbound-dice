"""Regression contract for default roll rendering.

This file is the regression contract; do not regenerate the snapshot JSON to
make it pass.
"""

import json
import random
from pathlib import Path

import pytest
from format_corpus import EXPRESSIONS, MODIFIER_CASES, SEED

from wyrdbound_dice import Dice

SNAPSHOT_PATH = Path(__file__).parent / "data" / "format_snapshots.json"

with SNAPSHOT_PATH.open(encoding="utf-8") as snapshot_file:
    SNAPSHOTS = json.load(snapshot_file)


def roll(expression, modifiers=None):
    """Roll one corpus entry, mirroring how the snapshots were generated."""
    try:
        result = Dice.roll(expression, modifiers=modifiers, rng=random.Random(SEED))
    except Exception as exc:  # noqa: BLE001 - snapshots pin the exception type
        return "!" + type(exc).__name__
    return str(result)


def expression_params():
    """Corpus expressions, keyed by the expression itself."""
    return [pytest.param(expression, id=expression) for expression in EXPRESSIONS]


def modifier_params():
    """Corpus modifier cases, keyed the way the snapshot file keys them."""
    params = []
    for expression, modifiers in MODIFIER_CASES:
        key = expression + " ||| " + json.dumps(modifiers, sort_keys=True)
        params.append(pytest.param(expression, modifiers, id=key))
    return params


@pytest.mark.parametrize("expression", expression_params())
def test_expression_snapshot(expression):
    """Render an expression and assert it matches the frozen snapshot."""
    expected = SNAPSHOTS[expression]
    actual = roll(expression)
    assert actual == expected, "key: {}\nexpected: {}\nactual: {}".format(
        expression, expected, actual
    )


@pytest.mark.parametrize("expression,modifiers", modifier_params())
def test_modifier_snapshot(expression, modifiers):
    """Render a modifier case and assert it matches the frozen snapshot."""
    key = expression + " ||| " + json.dumps(modifiers, sort_keys=True)
    expected = SNAPSHOTS[key]
    actual = roll(expression, modifiers)
    assert actual == expected, "key: {}\nexpected: {}\nactual: {}".format(
        key, expected, actual
    )
