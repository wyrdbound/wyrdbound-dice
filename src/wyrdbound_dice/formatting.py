"""Rendering options for roll breakdowns.

``RollFormat`` holds every display choice as a frozen field, so a format is
hashable, safe to share as a module default, and derivable with
``dataclasses.replace()``. Presets are ordinary instances defined at the bottom
of this module.

This module owns display policy only. The facts being displayed live in
:mod:`wyrdbound_dice.breakdown`.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Tuple, runtime_checkable

from .breakdown import RollBreakdown


class Dropped(Enum):
    """How dropped dice are rendered."""

    SHOWN = "shown"
    HIDDEN = "hidden"
    MARKED = "marked"


class Percentile(Enum):
    """How percentile dice are rendered."""

    PAIR = "pair"
    VALUE = "value"


@dataclass(frozen=True)
class RollFormat:
    """A frozen set of display choices for a roll.

    Every default reproduces the library's standard output, so
    ``RollFormat()`` and ``RollFormat.STANDARD`` are equal by construction.

    Attributes:
        layout: A template arranging the three top-level components. May use
            ``{total}``, ``{breakdown}`` and ``{expression}`` only.
        show_notation: Include the dice notation (for example ``2d6``) in a
            group. When ``False`` only the values render.
        dropped: Whether dropped dice are shown, hidden, or marked.
        show_rerolls: Render superseded reroll faces. Explosion faces always
            render because they contribute to the value.
        modifier_depth: ``0`` value only, ``1`` adds the name, ``2`` adds a
            nested roll. Above ``2`` behaves as ``2``.
        die_separator: String between dice within a group.
        group_open: Text opening a group's bracketed section.
        group_close: Text closing a group's bracketed section.
        notation_separator: String between the notation and the dice values.
        multiply_symbol: Glyph substituted for the canonical ``x`` operator.
        divide_symbol: Glyph substituted for the canonical ``/`` operator.
        dropped_marker: Template wrapping a dropped die's rendered text; may
            use ``{value}``.
        fudge_symbols: ``(minus, blank, plus)`` for raw Fudge faces 1-2, 3-4,
            5-6.
        percentile: Pair (``[00, 5]``) or single value (``05``) display.
    """

    layout: str = "{total} = {breakdown}"

    show_notation: bool = True
    dropped: Dropped = Dropped.SHOWN
    show_rerolls: bool = True
    modifier_depth: int = 2

    die_separator: str = ", "
    group_open: str = "("
    group_close: str = ")"
    notation_separator: str = ": "
    multiply_symbol: str = "x"
    divide_symbol: str = "/"
    dropped_marker: str = "~{value}~"
    fudge_symbols: Tuple[str, str, str] = ("-", "B", "+")
    percentile: Percentile = Percentile.PAIR

    def __post_init__(self) -> None:
        """Validate the layout template at construction time.

        Only ``{total}``, ``{breakdown}`` and ``{expression}`` are permitted, and
        at least one must be present. Only reads ``self``, so ``frozen=True``
        is preserved.
        """
        message = (
            "layout may only use {total}, {breakdown} and {expression}; "
            "got: " + repr(self.layout)
        )

        try:
            self.layout.format(total="", breakdown="", expression="")
        except (KeyError, IndexError, ValueError):
            raise ValueError(message)

        placeholders = ("{total}", "{breakdown}", "{expression}")
        if not any(placeholder in self.layout for placeholder in placeholders):
            raise ValueError(message)


@runtime_checkable
class Formatter(Protocol):
    """Structural interface for anything that renders a roll breakdown.

    Matches the duck-typed ``rng=`` precedent: an object satisfies this
    protocol if it has a compatible ``format`` method, with no inheritance
    required.
    """

    def format(self, breakdown: RollBreakdown) -> str:
        """Render a roll breakdown to a string."""
        ...
