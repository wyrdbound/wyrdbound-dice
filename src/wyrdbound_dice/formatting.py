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

from .breakdown import (
    PRECEDENCE,
    BinaryOp,
    DiceNode,
    Literal,
    RollBreakdown,
    UnaryOp,
)


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


class DefaultFormatter:
    """The standard renderer for a roll breakdown.

    Subclass and override any of the ``format_*`` hooks to change part of the
    output without reimplementing the whole fold.
    """

    def __init__(self, fmt: RollFormat = None) -> None:
        """Store the format this formatter renders with.

        Args:
            fmt: The display options. Defaults to ``RollFormat()``.
        """
        self.fmt = fmt if fmt is not None else RollFormat()

    def format_die(self, die, group) -> str:
        """Render one die's faces, joined by ``die_separator``.

        Fudge faces map through ``fudge_symbols`` at the raw thresholds
        (``<= 2`` minus, ``<= 4`` blank, else plus). Percentile faces render as
        a pair ``[tens, ones]`` or a single value per ``percentile``.

        Args:
            die: The :class:`~wyrdbound_dice.breakdown.Die` to render.
            group: The group the die belongs to, for its ``kind``.
        """
        rendered = []
        for face in die.faces:
            if group.kind == "fudge":
                if face <= 2:
                    rendered.append(self.fmt.fudge_symbols[0])
                elif face <= 4:
                    rendered.append(self.fmt.fudge_symbols[1])
                else:
                    rendered.append(self.fmt.fudge_symbols[2])
            elif group.kind == "percentile":
                rendered.append(self._format_percentile_face(face))
            else:
                rendered.append(str(face))
        return self.fmt.die_separator.join(rendered)

    def _format_percentile_face(self, face) -> str:
        """Render one percentile face as a pair or a single value."""
        if self.fmt.percentile == Percentile.VALUE:
            if isinstance(face, tuple) and len(face) == 2:
                tens, ones = face
                return str(tens + ones)
            return str(face)

        if isinstance(face, tuple) and len(face) == 2:
            tens, ones = face
            tens_str = "{}".format(tens).zfill(2) if tens < 100 else str(tens)
            return "[{}, {}]".format(tens_str, ones)
        return str(face)

    def format_group(self, group) -> str:
        """Render a dice group: total, notation and dice values.

        Omits the notation and its separator when ``show_notation`` is False,
        and omits the whole bracketed section when the group has no dice.

        Args:
            group: The :class:`~wyrdbound_dice.breakdown.DiceGroup` to render.
        """
        dice_text = self.fmt.die_separator.join(
            self.format_die(die, group) for die in group.dice
        )

        if not group.dice:
            return "{} {}{}{}".format(
                group.total, self.fmt.group_open, group.notation, self.fmt.group_close
            )

        if self.fmt.show_notation:
            inner = "{}{}{}".format(
                group.notation, self.fmt.notation_separator, dice_text
            )
        else:
            inner = dice_text

        return "{} {}{}{}".format(
            group.total, self.fmt.group_open, inner, self.fmt.group_close
        )

    def format_node(self, node, parent_precedence: int = 0) -> str:
        """Render an expression-tree node, parenthesising by precedence.

        A ``BinaryOp`` child is wrapped when its operator binds more loosely
        than the parent's, or equally loosely on the *right* of ``-`` or
        ``/``. The canonical ``x`` and ``/`` operators are substituted with
        the format's symbols at render time.

        Args:
            node: An expression-tree node.
            parent_precedence: The binding strength of the enclosing operator,
                or ``0`` at the root.
        """
        return self._format_node(node, parent_precedence, is_right=False)

    def _format_node(self, node, parent_precedence: int, is_right: bool) -> str:
        """Render a node, knowing whether it sits to a parent's right."""
        if isinstance(node, Literal):
            return str(node.value)

        if isinstance(node, DiceNode):
            return self.format_group(node.group)

        if isinstance(node, UnaryOp):
            return "{}{}".format(
                node.op, self._format_node(node.operand, 3, is_right=False)
            )

        if isinstance(node, BinaryOp):
            precedence = PRECEDENCE[node.op]
            left = self._format_node(node.left, precedence, is_right=False)
            right = self._format_node(node.right, precedence, is_right=True)
            rendered = "{} {} {}".format(left, self._operator_symbol(node.op), right)

            if self._needs_parentheses(node, parent_precedence, is_right):
                return "{}{}{}".format(
                    self.fmt.group_open, rendered, self.fmt.group_close
                )
            return rendered

        raise TypeError("unknown node type: {!r}".format(type(node).__name__))

    def _operator_symbol(self, op: str) -> str:
        """Substitute the format's glyph for a canonical operator."""
        if op == "x":
            return self.fmt.multiply_symbol
        if op == "/":
            return self.fmt.divide_symbol
        return op

    def _needs_parentheses(self, node, parent_precedence: int, is_right: bool) -> bool:
        """Decide whether a binary node needs wrapping given its parent.

        A child that binds more loosely than its parent needs brackets. A child
        that binds equally loosely needs them only on the right of ``-`` or
        ``/``, where left-to-right evaluation would otherwise change the
        meaning.
        """
        if parent_precedence == 0:
            return False

        precedence = PRECEDENCE[node.op]
        if precedence < parent_precedence:
            return True
        if precedence > parent_precedence:
            return False
        return is_right and node.op in ("-", "/")

    def format_modifier(self, modifier) -> str:
        """Render a named modifier honouring ``modifier_depth``.

        ``0`` renders the value only; ``1`` adds the name; ``2`` additionally
        renders a nested dice roll through the same layout. Above ``2`` behaves
        as ``2``. The sign sits outside the value and the nested roll shows its
        unsigned total, matching the established modifier output.

        Args:
            modifier: The :class:`~wyrdbound_dice.breakdown.ModifierBreakdown`
                to render.
        """
        sign = "+" if modifier.value >= 0 else "-"
        magnitude = abs(modifier.value)

        if self.fmt.modifier_depth <= 0:
            return "{} {}".format(sign, magnitude)

        base = "{} {}".format(sign, magnitude)
        if not modifier.name:
            return base

        if self.fmt.modifier_depth == 1 or modifier.nested is None:
            return "{} ({})".format(base, modifier.name)

        nested = self._render_nested(modifier.nested)
        return "{} ({}: {})".format(base, modifier.name, nested)

    def format(self, breakdown: RollBreakdown) -> str:
        """Render a full roll breakdown through the layout template.

        The breakdown body is only built when ``{breakdown}`` appears in the
        layout; otherwise the work is skipped entirely. The total is exposed as
        a component and the layout arranges it.

        Args:
            breakdown: The :class:`~wyrdbound_dice.breakdown.RollBreakdown` to
                render.
        """
        return self._apply_layout(breakdown.total, breakdown, breakdown.expression)

    def _render_nested(self, nested) -> str:
        """Render a modifier's nested roll, accepting a breakdown or a group."""
        if hasattr(nested, "root"):
            return self._apply_layout(nested.total, nested, nested.expression)
        return self.format_group(nested)

    def _apply_layout(self, total, breakdown_obj, expression: str) -> str:
        """Apply the layout template to already-rendered components.

        Only the layout string is parsed by ``str.format``; the component text
        is substituted in as literal output and never re-scanned. The breakdown
        is not rendered at all when ``{breakdown}`` is absent.
        """
        if "{breakdown}" in self.fmt.layout:
            body = self.format_node(breakdown_obj.root)
            for modifier in breakdown_obj.modifiers:
                body += " " + self.format_modifier(modifier)
        else:
            body = ""
        return self.fmt.layout.format(
            total=str(total), breakdown=body, expression=expression
        )
