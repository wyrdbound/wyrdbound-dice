from typing import List, Optional, Tuple

from .breakdown import DiceGroup, DiceNode, Die
from .errors import DivisionByZeroError


class KeepOperationProcessor:
    """Handles keep operation logic for dice rolls."""

    @staticmethod
    def apply_keep_operations(
        rolls: List[int], keep_operations: List[Tuple]
    ) -> Tuple[List[int], List[int]]:
        """
        Apply multiple keep operations sequentially and return
        (kept, dropped).
        """
        current_rolls = sorted(rolls)
        dropped = []

        for keep_type, keep_n in keep_operations:
            if keep_n == 0:
                # Special case: keeping 0 dice means keep none
                dropped.extend(current_rolls)
                current_rolls = []
                break
            elif keep_type.lower() == "h":
                current_rolls, newly_dropped = KeepOperationProcessor._keep_highest(
                    current_rolls, keep_n
                )
            else:  # keep_type.lower() == "l"
                current_rolls, newly_dropped = KeepOperationProcessor._keep_lowest(
                    current_rolls, keep_n
                )

            dropped.extend(newly_dropped)
            current_rolls = sorted(current_rolls)

        return current_rolls, dropped

    @staticmethod
    def _keep_highest(rolls: List[int], keep_n: int) -> Tuple[List[int], List[int]]:
        """Keep the highest N dice from sorted rolls."""
        if keep_n >= len(rolls):
            return rolls, []

        to_drop = rolls[:-keep_n]
        to_keep = rolls[-keep_n:]
        return to_keep, to_drop

    @staticmethod
    def _keep_lowest(rolls: List[int], keep_n: int) -> Tuple[List[int], List[int]]:
        """Keep the lowest N dice from sorted rolls."""
        if keep_n >= len(rolls):
            return rolls, []

        to_keep = rolls[:keep_n]
        to_drop = rolls[keep_n:]
        return to_keep, to_drop

    @staticmethod
    def apply_legacy_keep(
        rolls: List[int], keep_type: str, keep_n: int
    ) -> Tuple[List[int], List[int]]:
        """Apply a single legacy keep operation."""
        sorted_rolls = sorted(rolls)

        if keep_n == 0:
            return [], sorted_rolls
        elif keep_type.lower() == "h":
            return KeepOperationProcessor._keep_highest(sorted_rolls, keep_n)
        else:
            return KeepOperationProcessor._keep_lowest(sorted_rolls, keep_n)

    @staticmethod
    def apply_drop_operations(
        rolls: List[int], drop_operations: List[Tuple]
    ) -> Tuple[List[int], List[int]]:
        """
        Apply multiple drop operations sequentially and
        return (kept, dropped).
        """
        current_rolls = sorted(rolls)
        dropped = []

        for drop_type, drop_n in drop_operations:
            if drop_n == 0:
                # Special case: dropping 0 dice means drop none
                continue
            elif drop_type.lower() == "h":
                current_rolls, newly_dropped = KeepOperationProcessor._drop_highest(
                    current_rolls, drop_n
                )
            else:  # drop_type.lower() == "l"
                current_rolls, newly_dropped = KeepOperationProcessor._drop_lowest(
                    current_rolls, drop_n
                )

            dropped.extend(newly_dropped)
            current_rolls = sorted(current_rolls)

        return current_rolls, dropped

    @staticmethod
    def _drop_highest(rolls: List[int], drop_n: int) -> Tuple[List[int], List[int]]:
        """Drop the highest N dice from sorted rolls."""
        if drop_n >= len(rolls):
            return [], rolls

        to_drop = rolls[-drop_n:]
        to_keep = rolls[:-drop_n]
        return to_keep, to_drop

    @staticmethod
    def _drop_lowest(rolls: List[int], drop_n: int) -> Tuple[List[int], List[int]]:
        """Drop the lowest N dice from sorted rolls."""
        if drop_n >= len(rolls):
            return [], rolls

        to_keep = rolls[drop_n:]
        to_drop = rolls[:drop_n]
        return to_keep, to_drop

    @staticmethod
    def _sorted_pairs(rolls: List[int]) -> List[Tuple[int, int]]:
        """Pair each die with its original position, ordered by value.

        The sort is stable, so ties keep their original relative order — which
        is what makes an index-based dropped die deterministic when two dice
        share a value.
        """
        return sorted(enumerate(rolls), key=lambda p: p[1])

    @staticmethod
    def apply_keep_operations_indexed(
        rolls: List[int], keep_operations: List[Tuple]
    ) -> Tuple[List[int], List[int]]:
        """Apply keep operations and return (kept_indices, dropped_indices)."""
        current_pairs = KeepOperationProcessor._sorted_pairs(rolls)
        dropped_pairs = []

        for keep_type, keep_n in keep_operations:
            if keep_n == 0:
                dropped_pairs.extend(current_pairs)
                current_pairs = []
                break
            elif keep_type.lower() == "h":
                current_pairs, newly_dropped = (
                    KeepOperationProcessor._keep_highest_indexed(current_pairs, keep_n)
                )
            else:  # keep_type.lower() == "l"
                current_pairs, newly_dropped = (
                    KeepOperationProcessor._keep_lowest_indexed(current_pairs, keep_n)
                )

            dropped_pairs.extend(newly_dropped)
            current_pairs = sorted(current_pairs, key=lambda p: p[1])

        return (
            [index for index, _ in current_pairs],
            [index for index, _ in dropped_pairs],
        )

    @staticmethod
    def _keep_highest_indexed(
        pairs: List[Tuple[int, int]], keep_n: int
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Keep the highest N dice from value-sorted pairs."""
        if keep_n >= len(pairs):
            return pairs, []

        to_drop = pairs[:-keep_n]
        to_keep = pairs[-keep_n:]
        return to_keep, to_drop

    @staticmethod
    def _keep_lowest_indexed(
        pairs: List[Tuple[int, int]], keep_n: int
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Keep the lowest N dice from value-sorted pairs."""
        if keep_n >= len(pairs):
            return pairs, []

        to_keep = pairs[:keep_n]
        to_drop = pairs[keep_n:]
        return to_keep, to_drop

    @staticmethod
    def apply_legacy_keep_indexed(
        rolls: List[int], keep_type: str, keep_n: int
    ) -> Tuple[List[int], List[int]]:
        """Apply a single legacy keep operation, returning indices."""
        sorted_pairs = KeepOperationProcessor._sorted_pairs(rolls)

        if keep_n == 0:
            kept_pairs, dropped_pairs = [], sorted_pairs
        elif keep_type.lower() == "h":
            kept_pairs, dropped_pairs = KeepOperationProcessor._keep_highest_indexed(
                sorted_pairs, keep_n
            )
        else:
            kept_pairs, dropped_pairs = KeepOperationProcessor._keep_lowest_indexed(
                sorted_pairs, keep_n
            )

        return (
            [index for index, _ in kept_pairs],
            [index for index, _ in dropped_pairs],
        )

    @staticmethod
    def apply_drop_operations_indexed(
        rolls: List[int], drop_operations: List[Tuple]
    ) -> Tuple[List[int], List[int]]:
        """Apply drop operations and return (kept_indices, dropped_indices)."""
        current_pairs = KeepOperationProcessor._sorted_pairs(rolls)
        dropped_pairs = []

        for drop_type, drop_n in drop_operations:
            if drop_n == 0:
                continue
            elif drop_type.lower() == "h":
                current_pairs, newly_dropped = (
                    KeepOperationProcessor._drop_highest_indexed(current_pairs, drop_n)
                )
            else:  # drop_type.lower() == "l"
                current_pairs, newly_dropped = (
                    KeepOperationProcessor._drop_lowest_indexed(current_pairs, drop_n)
                )

            dropped_pairs.extend(newly_dropped)
            current_pairs = sorted(current_pairs, key=lambda p: p[1])

        return (
            [index for index, _ in current_pairs],
            [index for index, _ in dropped_pairs],
        )

    @staticmethod
    def _drop_highest_indexed(
        pairs: List[Tuple[int, int]], drop_n: int
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Drop the highest N dice from value-sorted pairs."""
        if drop_n >= len(pairs):
            return [], pairs

        to_drop = pairs[-drop_n:]
        to_keep = pairs[:-drop_n]
        return to_keep, to_drop

    @staticmethod
    def _drop_lowest_indexed(
        pairs: List[Tuple[int, int]], drop_n: int
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Drop the lowest N dice from value-sorted pairs."""
        if drop_n >= len(pairs):
            return [], pairs

        to_keep = pairs[drop_n:]
        to_drop = pairs[:drop_n]
        return to_keep, to_drop


class RollResult:
    def __init__(
        self,
        num: int,
        sides,  # Can be int or str (for Fudge dice "F" or Percentile dice "%")
        rolls: List[int],
        keep_type: Optional[str] = None,
        keep_n: Optional[int] = None,
        reroll_count: Optional[str] = None,
        reroll_cmp: Optional[str] = None,
        reroll_target: Optional[int] = None,
        all_rolls: Optional[List[int]] = None,
        multiply: Optional[int] = None,
        divide: Optional[int] = None,
        explode_target: Optional[int] = None,
        explode_cmp: Optional[str] = None,
        is_fudge: bool = False,
        is_percentile: bool = False,
        keep_operations: Optional[List[Tuple]] = None,
        drop_operations: Optional[List[Tuple]] = None,
        dice_traces: Optional[List[dict]] = None,
    ):
        # Basic attributes
        self.num = num
        self.sides = sides
        self.rolls = rolls
        self.all_rolls = all_rolls or rolls
        self.multiply = multiply or 1
        self.divide = divide or 1
        self.is_fudge = is_fudge
        self.is_percentile = is_percentile

        # Keep operation attributes
        self.keep_type = keep_type
        self.keep_n = keep_n
        self.keep_operations = keep_operations or []
        self.drop_operations = drop_operations or []

        # Reroll attributes
        self.reroll_count = reroll_count
        self.reroll_cmp = reroll_cmp
        self.reroll_target = reroll_target

        # Exploding dice attributes
        self.explode_target = explode_target
        self.explode_cmp = explode_cmp

        # Cross-dice operation attributes
        self._cross_dice_op = None
        self._cross_dice_result = None

        # Calculate kept and dropped dice
        self._calculate_kept_and_dropped()

        # Per-die provenance. Results built without tracing (flux results take
        # this path) synthesise one face per die so the shape is uniform.
        if dice_traces is None:
            faces_source = (
                self.all_rolls if len(self.all_rolls) == len(self.rolls) else self.rolls
            )
            dice_traces = [
                {"faces": [value], "sources": ["roll"], "value": value}
                for value in faces_source
            ]
        self.dice_traces = dice_traces

    @property
    def subtotal(self) -> int:
        return sum(self.kept)

    @property
    def breakdown(self) -> DiceGroup:
        """Return this result as a structured :class:`DiceGroup`.

        The notation follows the display order keep, drop, reroll, explode.
        ``kept`` on each die comes from ``kept_indices``, so a dropped die is
        identified by position rather than by value.
        """
        if self.is_fudge:
            kind = "fudge"
        elif self.is_percentile:
            kind = "percentile"
        else:
            kind = "standard"

        notation = (
            f"{self.num}d{self.sides}"
            + self._build_keep_string()
            + self._build_drop_string()
            + self._build_reroll_string()
            + self._build_explode_string()
        )

        kept_index_set = set(self.kept_indices)
        dice = tuple(
            Die(
                value=trace["value"],
                faces=tuple(trace["faces"]),
                sources=tuple(trace["sources"]),
                kept=index in kept_index_set,
            )
            for index, trace in enumerate(self.dice_traces)
        )

        reroll = (
            (self.reroll_count, self.reroll_cmp, self.reroll_target)
            if self.reroll_target is not None
            else None
        )
        explode = (
            (self.explode_cmp, self.explode_target)
            if self.explode_target is not None
            else None
        )

        kept_sum = sum(self.kept)
        if self.divide == 0:
            raise DivisionByZeroError()
        return DiceGroup(
            num=self.num,
            sides=str(self.sides),
            kind=kind,
            notation=notation,
            dice=dice,
            keep_operations=tuple(tuple(op) for op in self.keep_operations),
            drop_operations=tuple(tuple(op) for op in self.drop_operations),
            reroll=reroll,
            explode=explode,
            subtotal=kept_sum,
            total=(kept_sum * self.multiply) // self.divide,
        )

    def __str__(self):
        """Return a formatted string representation of the roll result."""
        from .formatting import DefaultFormatter, RollFormat

        return DefaultFormatter(RollFormat(layout="{breakdown}")).format_node(
            self.to_node()
        )

    def _build_keep_string(self) -> str:
        """Build the keep operations string for display."""
        if self.keep_operations:
            return "".join(
                f"k{keep_type}{keep_n}" for keep_type, keep_n in self.keep_operations
            )
        elif self.keep_type:
            return f"k{self.keep_type}{self.keep_n}"
        return ""

    def _build_reroll_string(self) -> str:
        """Build the reroll string for display."""
        if (
            self.reroll_count is not None
            and self.reroll_cmp
            and self.reroll_target is not None
        ):
            return f"r{self.reroll_count}{self.reroll_cmp}{self.reroll_target}"
        return ""

    def _build_explode_string(self) -> str:
        """Build the explode string for display."""
        if self.explode_target is not None:
            if self.explode_cmp:
                return f"e{self.explode_cmp}{self.explode_target}"
            else:
                return f"e{self.explode_target}"
        return ""

    def _calculate_kept_and_dropped(self) -> None:
        """
        Calculate which dice are kept and which are dropped based
        on keep/drop operations.
        """
        if self.drop_operations:
            # Apply drop operations
            self.kept_indices, self.dropped_indices = (
                KeepOperationProcessor.apply_drop_operations_indexed(
                    self.rolls, self.drop_operations
                )
            )
        elif self.keep_operations:
            # Apply keep operations
            self.kept_indices, self.dropped_indices = (
                KeepOperationProcessor.apply_keep_operations_indexed(
                    self.rolls, self.keep_operations
                )
            )
        elif self.keep_type and self.keep_n is not None:
            # Apply legacy keep operations
            self.kept_indices, self.dropped_indices = (
                KeepOperationProcessor.apply_legacy_keep_indexed(
                    self.rolls, self.keep_type, self.keep_n
                )
            )
        else:
            # No operations - keep all dice
            self.kept_indices = list(range(len(self.rolls)))
            self.dropped_indices = []

        self.kept = [self.rolls[i] for i in sorted(self.kept_indices)]
        self.dropped = [self.rolls[i] for i in sorted(self.dropped_indices)]

    def _build_drop_string(self) -> str:
        """Build the drop operations string for display."""
        if self.drop_operations:
            return "".join(
                f"d{drop_type}{drop_n}" for drop_type, drop_n in self.drop_operations
            )
        return ""

    def to_node(self) -> DiceNode:
        """Return this result as a :class:`DiceNode` in the expression tree."""
        return DiceNode(self.breakdown)
