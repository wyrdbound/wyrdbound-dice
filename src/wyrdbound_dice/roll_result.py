from typing import List, Optional, Tuple

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


class FudgeDiceFormatter:
    """Handles formatting of Fudge dice values."""

    @staticmethod
    def format_fudge_values(raw_rolls: List[int]) -> List[str]:
        """Convert raw Fudge dice rolls to display values."""
        fudge_values = []
        for raw_roll in raw_rolls:
            if raw_roll <= 2:
                fudge_values.append("-")
            elif raw_roll <= 4:
                fudge_values.append("B")
            else:
                fudge_values.append("+")
        return fudge_values


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

    @property
    def subtotal(self) -> int:
        return sum(self.kept)

    def __str__(self):
        """Return a formatted string representation of the roll result."""
        # Build modifier strings
        keep_str = self._build_keep_string()
        drop_str = self._build_drop_string()
        reroll_str = self._build_reroll_string()
        explode_str = self._build_explode_string()

        # Format rolls display
        rolls_str = self._format_rolls_display()

        # Calculate total with math operations
        kept_sum = sum(self.kept)
        if self.divide == 0:
            raise DivisionByZeroError()
        total_with_math = (kept_sum * self.multiply) // self.divide

        # Handle cross-dice operations
        cross_dice_str = self._build_cross_dice_string(
            kept_sum, keep_str, drop_str, reroll_str, explode_str, rolls_str
        )
        if cross_dice_str:
            return cross_dice_str

        # Handle multiplication/division for static values
        math_operation_str = self._build_math_operation_string(
            kept_sum, keep_str, drop_str, reroll_str, explode_str, rolls_str
        )
        if math_operation_str:
            return math_operation_str

        # Default format
        if rolls_str:
            return (
                f"{total_with_math} ({self.num}d{self.sides}{keep_str}"
                + f"{drop_str}{reroll_str}{explode_str}: {rolls_str})"
            )
        else:
            return (
                f"{total_with_math} ({self.num}d{self.sides}{keep_str}"
                + f"{drop_str}{reroll_str}{explode_str})"
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

    def _format_rolls_display(self) -> str:
        """
        Format the rolls for display, handling Fudge dice and
        percentile dice specially.
        """
        if self.is_fudge:
            fudge_values = FudgeDiceFormatter.format_fudge_values(self.all_rolls)
            return ", ".join(fudge_values)
        elif self.is_percentile:
            # Format percentile dice as [tens, ones]
            percentile_values = []
            for roll in self.all_rolls:
                if isinstance(roll, tuple) and len(roll) == 2:
                    tens, ones = roll
                    tens_str = f"{tens:02d}" if tens < 100 else str(tens)
                    ones_str = f"{ones}"
                    percentile_values.append(f"[{tens_str}, {ones_str}]")
                else:
                    # Fallback for non-tuple values (shouldn't happen with
                    # percentile)
                    percentile_values.append(str(roll))
            return ", ".join(percentile_values)
        else:
            return ", ".join(str(r) for r in self.all_rolls)

    def _build_cross_dice_string(
        self,
        kept_sum: int,
        keep_str: str,
        drop_str: str,
        reroll_str: str,
        explode_str: str,
        rolls_str: str,
    ) -> Optional[str]:
        """Build string for cross-dice operations."""
        if not (self._cross_dice_op and self._cross_dice_result):
            return None

        cross_dice_rolls = ", ".join(str(r) for r in self._cross_dice_result.all_rolls)
        cross_dice_total = self._cross_dice_result.subtotal
        dice_part = (
            f"{self.num}d{self.sides}{keep_str}{drop_str}"
            + f"{reroll_str}{explode_str}: {rolls_str}"
        )
        cross_part = (
            f"{self._cross_dice_result.num}d"
            + f"{self._cross_dice_result.sides}: {cross_dice_rolls}"
        )

        if self._cross_dice_op == "multiply":
            return f"{kept_sum} ({dice_part}) x {cross_dice_total} ({cross_part})"
        elif self._cross_dice_op == "divide":
            return f"{kept_sum} ({dice_part}) / {cross_dice_total} ({cross_part})"

        return None

    def _build_math_operation_string(
        self,
        kept_sum: int,
        keep_str: str,
        drop_str: str,
        reroll_str: str,
        explode_str: str,
        rolls_str: str,
    ) -> Optional[str]:
        """Build string for math operations with static values."""
        if self.multiply > 1:
            dice_part = (
                f"{self.num}d{self.sides}{keep_str}{drop_str}"
                + f"{reroll_str}{explode_str}: {rolls_str}"
            )
            return f"{kept_sum} ({dice_part}) x {self.multiply}"
        elif self.divide > 1:
            dice_part = (
                f"{self.num}d{self.sides}{keep_str}{drop_str}"
                + f"{reroll_str}{explode_str}: {rolls_str}"
            )
            return f"{kept_sum} ({dice_part}) / {self.divide}"

        return None

    def _calculate_kept_and_dropped(self) -> None:
        """
        Calculate which dice are kept and which are dropped based
        on keep/drop operations.
        """
        if self.drop_operations:
            # Apply drop operations
            self.kept, self.dropped = KeepOperationProcessor.apply_drop_operations(
                self.rolls, self.drop_operations
            )
        elif self.keep_operations:
            # Apply keep operations
            self.kept, self.dropped = KeepOperationProcessor.apply_keep_operations(
                self.rolls, self.keep_operations
            )
        elif self.keep_type and self.keep_n is not None:
            # Apply legacy keep operations
            self.kept, self.dropped = KeepOperationProcessor.apply_legacy_keep(
                self.rolls, self.keep_type, self.keep_n
            )
        else:
            # No operations - keep all dice
            self.kept = self.rolls
            self.dropped = []

    def _build_drop_string(self) -> str:
        """Build the drop operations string for display."""
        if self.drop_operations:
            return "".join(
                f"d{drop_type}{drop_n}" for drop_type, drop_n in self.drop_operations
            )
        return ""
