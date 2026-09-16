"""Rendering options for roll breakdowns.

``RollFormat`` holds every display choice as a frozen field, so a format is
hashable, safe to share as a module default, and derivable with
``dataclasses.replace()``. Presets are ordinary instances defined at the bottom
of this module.

This module owns display policy only. The facts being displayed live in
:mod:`wyrdbound_dice.breakdown`.
"""

import re
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

LAYOUT_FIELDS = ("total", "breakdown", "expression")
MARKER_FIELDS = ("value",)


def _template_pattern(fields):
    """Build the scanner for a template that admits exactly ``fields``.

    The pattern matches the two brace escapes and nothing else that is
    brace-shaped, so anything it does not match is a validation failure.
    """
    return re.compile(r"\{\{|\}\}|\{(" + "|".join(fields) + r")\}")


_LAYOUT_RE = _template_pattern(LAYOUT_FIELDS)
_MARKER_RE = _template_pattern(MARKER_FIELDS)


def _validate_template(template, pattern, fields, name):
    """Reject any template this module would not substitute literally.

    ``str.format`` accepts far more than a field name: attribute access
    (``{total.__class__}``), indexing, and format specs with unbounded width
    (``{value:>100000000}``). None of that is display configuration, and all of
    it reaches through a component into the interpreter. This permits only a
    bare ``{field}`` for a known field, plus the ``{{`` and ``}}`` escapes.

    Args:
        template: The candidate template string.
        pattern: The scanner from :func:`_template_pattern`.
        fields: The field names this template may name.
        name: The attribute name, for the error message.

    Returns:
        The list of field names the template actually uses.

    Raises:
        ValueError: If the template is not a string, or contains any brace
            construct other than a permitted placeholder or escape.
    """
    allowed = ", ".join("{" + field + "}" for field in fields)
    if not isinstance(template, str):
        raise ValueError(
            name
            + " must be a string using only "
            + allowed
            + "; got: "
            + repr(template)
        )

    residue = pattern.sub("", template)
    if "{" in residue or "}" in residue:
        raise ValueError(
            name
            + " may only use "
            + allowed
            + " and the escapes {{ and }}; got: "
            + repr(template)
        )

    return [match.group(1) for match in pattern.finditer(template) if match.group(1)]


def _render_template(template, pattern, values):
    """Substitute already-rendered components into a validated template.

    One pass, and ``re.sub`` never rescans what a replacement produced, so a
    brace inside a rendered component is literal output rather than a new
    placeholder.
    """

    def replace(match):
        field = match.group(1)
        if field is None:
            return "{" if match.group(0) == "{{" else "}"
        return values[field]

    return pattern.sub(replace, template)


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
            ``{total}``, ``{breakdown}`` and ``{expression}`` only, plus the
            ``{{`` and ``}}`` escapes. Attribute access and format specs are
            rejected at construction time.
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
            use ``{value}`` only, on the same terms as ``layout``.
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
        """Validate every field a caller could turn into a render-time fault.

        ``layout`` and ``dropped_marker`` are templates and are checked against
        :func:`_validate_template`; ``fudge_symbols`` is indexed by position at
        render time and so must be exactly three strings. Validating here means
        a bad format fails where it was written, and that formatting a
        successfully-evaluated roll never raises. Only reads ``self``, so
        ``frozen=True`` is preserved.

        Raises:
            ValueError: If any of those three fields could fault at render time.
        """
        used = _validate_template(self.layout, _LAYOUT_RE, LAYOUT_FIELDS, "layout")
        if not used:
            raise ValueError(
                "layout must use at least one of {total}, {breakdown}, "
                "{expression}; got: " + repr(self.layout)
            )

        _validate_template(
            self.dropped_marker, _MARKER_RE, MARKER_FIELDS, "dropped_marker"
        )

        if (
            not isinstance(self.fudge_symbols, tuple)
            or len(self.fudge_symbols) != 3
            or not all(isinstance(symbol, str) for symbol in self.fudge_symbols)
        ):
            raise ValueError(
                "fudge_symbols must be a tuple of exactly three strings "
                "(minus, blank, plus); got: " + repr(self.fudge_symbols)
            )


RollFormat.STANDARD = RollFormat()
RollFormat.MINIMAL = RollFormat(layout="{total}")
RollFormat.COMPACT = RollFormat(
    die_separator=",",
    notation_separator=":",
    modifier_depth=1,
    dropped=Dropped.HIDDEN,
    show_rerolls=False,
)
RollFormat.VERBOSE = RollFormat(dropped=Dropped.MARKED)

_DEFAULT_FORMAT = None


def set_default_format(fmt) -> None:
    """Set the module default format used by ``RollResultSet.format()``.

    This is display state read only at render time. It does **not** affect
    ``__str__``, which always renders ``RollFormat.STANDARD``. It is intended
    to be set once at application startup: it is not synchronised and not
    per-thread. Pass ``None`` to restore the standard format.

    Args:
        fmt: A :class:`RollFormat`, or ``None`` to unset.
    """
    global _DEFAULT_FORMAT
    _DEFAULT_FORMAT = fmt


def get_default_format() -> RollFormat:
    """Return the module default format, or ``RollFormat.STANDARD`` if unset."""
    return _DEFAULT_FORMAT if _DEFAULT_FORMAT is not None else RollFormat.STANDARD


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

        When ``show_rerolls`` is ``False`` only the die's final face renders
        for a rerolled die. **Explosion faces always render**, because every
        explosion face contributes to the die's value whereas a superseded
        reroll does not.

        Args:
            die: The :class:`~wyrdbound_dice.breakdown.Die` to render.
            group: The group the die belongs to, for its ``kind``.
        """
        faces = self._visible_faces(die)

        rendered = []
        for face in faces:
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

    def _visible_faces(self, die):
        """Return the faces to render for a die under ``show_rerolls``.

        Explosion faces are always kept: they are added to the value, unlike a
        reroll face that was superseded.
        """
        if self.fmt.show_rerolls:
            return list(die.faces)

        kept_faces = []
        for index, face in enumerate(die.faces):
            source = die.sources[index] if index < len(die.sources) else "roll"
            is_last = index == len(die.faces) - 1
            if source == "explosion" or is_last:
                kept_faces.append(face)
        return kept_faces

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
        Honour ``dropped``: ``HIDDEN`` omits a dropped die entirely, ``MARKED``
        wraps its rendered text with ``dropped_marker``, ``SHOWN`` renders it
        like any other die.

        Args:
            group: The :class:`~wyrdbound_dice.breakdown.DiceGroup` to render.
        """
        visible = [die for die in group.dice if not self._omit_die(die)]

        dice_text = self.fmt.die_separator.join(
            self._render_die(die, group) for die in visible
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

    def _omit_die(self, die) -> bool:
        """Whether a die is dropped and hidden."""
        return not die.kept and self.fmt.dropped == Dropped.HIDDEN

    def _render_die(self, die, group) -> str:
        """Render a die, marking it when it was dropped and MARKED is set."""
        text = self.format_die(die, group)
        if not die.kept and self.fmt.dropped == Dropped.MARKED:
            return _render_template(
                self.fmt.dropped_marker, _MARKER_RE, {"value": text}
            )
        return text

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
            symbol = self._operator_symbol(node.op)

            if node.op in ("+", "-") and right.startswith("-"):
                right = right[1:]
                symbol = "-" if node.op == "+" else "+"

            rendered = "{} {} {}".format(left, symbol, right)

            if self._needs_parentheses(node, parent_precedence, is_right):
                return "{}{}{}".format(
                    self.fmt.group_open, rendered, self.fmt.group_close
                )
            return rendered

        raise TypeError("unknown node type: {!r}".format(type(node).__name__))

    def _node_value(self, node) -> int:
        """Return the integer value a node evaluates to."""
        if isinstance(node, Literal):
            return node.value
        if isinstance(node, DiceNode):
            return node.group.total
        return node.value

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
        return _render_template(
            self.fmt.layout,
            _LAYOUT_RE,
            {
                "total": str(total),
                "breakdown": body,
                "expression": expression,
            },
        )
