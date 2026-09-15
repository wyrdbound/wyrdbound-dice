"""Tests for the structured roll breakdown."""

import random

from wyrdbound_dice import Dice


def roll(expr, seed=42, **kw):
    """Roll an expression with a fixed seed."""
    return Dice.roll(expr, rng=random.Random(seed), **kw)
