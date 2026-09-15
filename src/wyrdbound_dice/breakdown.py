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
    nested: Optional["RollBreakdown"] = None


@dataclass(frozen=True)
class RollBreakdown:
    """The complete structured record of a roll."""

    root: Node
    total: int
    expression: str = ""
    modifiers: Tuple[ModifierBreakdown, ...] = ()

    def to_dict(self):
        """Return a JSON-serialisable dict of this breakdown.

        No enums, tuples or dataclasses survive into the output, so the result
        can be passed straight to :func:`json.dumps` without a custom encoder.
        """
        return {
            "root": _node_to_dict(self.root),
            "total": self.total,
            "expression": self.expression,
            "modifiers": [_modifier_to_dict(modifier) for modifier in self.modifiers],
        }


def _die_to_dict(die):
    """Serialise one :class:`Die`."""
    return {
        "value": die.value,
        "faces": [_face_to_dict(face) for face in die.faces],
        "sources": list(die.sources),
        "kept": die.kept,
    }


def _face_to_dict(face):
    """Serialise one face, expanding percentile tuples into lists."""
    if isinstance(face, tuple):
        return list(face)
    return face


def _group_to_dict(group):
    """Serialise one :class:`DiceGroup`."""
    return {
        "num": group.num,
        "sides": group.sides,
        "kind": group.kind,
        "notation": group.notation,
        "dice": [_die_to_dict(die) for die in group.dice],
        "keep_operations": [list(op) for op in group.keep_operations],
        "drop_operations": [list(op) for op in group.drop_operations],
        "reroll": list(group.reroll) if group.reroll is not None else None,
        "explode": list(group.explode) if group.explode is not None else None,
        "subtotal": group.subtotal,
        "total": group.total,
    }


def _modifier_to_dict(modifier):
    """Serialise one :class:`ModifierBreakdown`."""
    if modifier.nested is not None:
        nested = modifier.nested.to_dict()
    else:
        nested = None
    return {
        "name": modifier.name,
        "value": modifier.value,
        "nested": nested,
    }


def _node_to_dict(node):
    """Serialise an expression-tree node, tagged by its ``type``."""
    if isinstance(node, Literal):
        return {"type": "literal", "value": node.value}
    if isinstance(node, DiceNode):
        return {"type": "dice", "group": _group_to_dict(node.group)}
    if isinstance(node, UnaryOp):
        return {
            "type": "unary",
            "op": node.op,
            "operand": _node_to_dict(node.operand),
            "value": node.value,
        }
    if isinstance(node, BinaryOp):
        return {
            "type": "binary",
            "left": _node_to_dict(node.left),
            "op": node.op,
            "right": _node_to_dict(node.right),
            "value": node.value,
        }
    raise TypeError("unknown node type: {!r}".format(type(node).__name__))
