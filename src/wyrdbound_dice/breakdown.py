"""Structured breakdown of a roll.

The breakdown is the roll; formatting is a view of it. This module holds the
types that describe *what happened* -- the per-die faces and their provenance,
the keep/drop outcome, and the evaluated expression tree -- with no rendering
policy. Formatters fold over these objects.

Nothing here is computed during rolling except the facts the roll loop already
knows; the types are frozen so a breakdown is safe to share and hash.
"""

from dataclasses import dataclass
from typing import Any, Optional, Tuple, Union

PRECEDENCE = {"+": 1, "-": 1, "x": 2, "/": 2}


@dataclass(frozen=True)
class Die:
    """One die in a group, with every face rolled for it.

    ``faces`` are the values rolled in order and ``sources`` is parallel to it,
    each entry being ``"roll"``, ``"reroll"`` or ``"explosion"``. ``value`` is
    this die's contribution to the subtotal (explosion faces already summed in).
    Concatenating ``faces`` across a group's dice in order reproduces that
    group's ``all_rolls`` exactly.
    """

    value: int
    faces: Tuple[Any, ...] = ()
    sources: Tuple[str, ...] = ()
    kept: bool = True


@dataclass(frozen=True)
class DiceGroup:
    """A single dice expression and its outcome."""

    num: int
    sides: str
    kind: str = "standard"
    notation: str = ""
    dice: Tuple[Die, ...] = ()
    keep_operations: Tuple[Tuple[str, int], ...] = ()
    drop_operations: Tuple[Tuple[str, int], ...] = ()
    reroll: Optional[Tuple[Optional[str], Optional[str], Optional[int]]] = None
    explode: Optional[Tuple[Optional[str], Optional[int]]] = None
    subtotal: int = 0
    total: int = 0


@dataclass(frozen=True)
class Literal:
    """A bare integer in the expression tree."""

    value: int


@dataclass(frozen=True)
class DiceNode:
    """A dice group used as an operand in the expression tree."""

    group: DiceGroup


@dataclass(frozen=True)
class UnaryOp:
    """A unary operation applied to an operand."""

    op: str
    operand: "Node"
    value: int


@dataclass(frozen=True)
class BinaryOp:
    """A binary operation joining two operands."""

    left: "Node"
    op: str
    right: "Node"
    value: int


Node = Union[Literal, DiceNode, UnaryOp, BinaryOp]


@dataclass(frozen=True)
class ModifierBreakdown:
    """A named modifier applied to a roll.

    ``nested`` carries the breakdown of a modifier that is itself a dice
    expression; it is ``None`` for a static modifier.
    """

    name: str = ""
    value: int = 0
    nested: Optional[DiceGroup] = None


@dataclass(frozen=True)
class RollBreakdown:
    """The complete structured record of a roll."""

    root: Node
    total: int
    expression: str = ""
    modifiers: Tuple[ModifierBreakdown, ...] = ()
