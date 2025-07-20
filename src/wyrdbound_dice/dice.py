import random
import re
from typing import Callable, Dict, List, Optional, Tuple, Union

from .errors import DivisionByZeroError, InfiniteConditionError, ParseError
from .expression_lexer import ExpressionLexer
from .expression_parser import ExpressionParser
from .expression_token import TokenType
from .roll_result import RollResult

# Constants
FUDGE_SIDES = 6
FUDGE_NEGATIVE_MAX = 2
FUDGE_BLANK_MAX = 4
DEFAULT_KEEP_COUNT = 1

# Dice system shorthand expansions
SHORTHAND_EXPANSIONS = {
    "FUDGE": "4dF",
    "BOON": "3d6kh2",
    "BANE": "3d6kl2",
    "FLUX": "1d6 - 1d6",
    "PERC": "1d%",
    "PERCENTILE": "1d%",
}

# Comparison operators for dice conditions
COMPARISON_OPERATORS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "=": lambda a, b: a == b,
}


class RollModifier:
    """Represents a modifier that can be either a static value or a dice
    expression."""

    def __init__(self, value: Union[int, str], description: Optional[str] = None):
        self.raw_value = value
        self.description = description or ""
        self.dice_result: Optional["RollResultSet"] = None

        if isinstance(value, int):
            self._init_static_modifier(value)
        else:
            self._init_dice_modifier(str(value))

    def _init_static_modifier(self, value: int) -> None:
        """Initialize a static integer modifier."""
        self.sign = "+" if value >= 0 else "-"
        self.value = value
        self.is_dice = False

    def _init_dice_modifier(self, value_str: str) -> None:
        """Initialize a dice expression modifier."""
        self.is_dice = True
        self.value = 0  # Will be set when rolled

        value_str = value_str.strip()
        if value_str.startswith("-"):
            self.sign = "-"
            self.dice_expression = value_str[1:]  # Remove the minus
        else:
            self.sign = "+"
            self.dice_expression = value_str.lstrip("+")  # Remove optional plus

    def roll(self, dice_class=None) -> None:
        """Roll the modifier if it's a dice expression."""
        if not self.is_dice or self.dice_result is not None:
            return

        if dice_class is None:
            raise ValueError("Dice class must be provided to roll dice modifiers")

        self.dice_result = dice_class.roll(self.dice_expression)
        self.value = self.dice_result.total
        if self.sign == "-":
            self.value = -self.value

    def __str__(self) -> str:
        """Return a string representation of the modifier."""
        if self.is_dice and self.dice_result:
            result = f"{self.sign} {self.dice_result.total}"
            dice_info = (
                f"{self.description}: {self.dice_result}"
                if self.description
                else str(self.dice_result)
            )
            return f"{result} ({dice_info})"
        else:
            result = f"{self.sign} {abs(self.value)}"
            return f"{result} ({self.description})" if self.description else result


class RollResultSet:
    """Represents a collection of dice roll results with optional modifiers."""

    def __init__(
        self,
        results: List[RollResult],
        modifiers: List[RollModifier] = None,
        dice_class=None,
    ):
        self.results = results
        self.modifiers = modifiers or []
        self._override_total: Optional[int] = None
        self._override_description: Optional[str] = None

        # Roll any dice modifiers
        for modifier in self.modifiers:
            modifier.roll(dice_class)

    @property
    def subtotal(self) -> int:
        """Calculate the subtotal from all dice results before applying
        modifiers."""
        total = 0
        for result in self.results:
            if result.divide == 0:
                raise DivisionByZeroError()
            total += (sum(result.kept) * result.multiply) // result.divide
        return total

    @property
    def total(self) -> int:
        """Calculate the final total including modifiers."""
        if self._override_total is not None:
            return self._override_total
        return self.subtotal + sum(modifier.value for modifier in self.modifiers)

    def __str__(self) -> str:
        """Return a formatted string representation of the roll result."""
        if self._override_description is not None:
            return f"{self.total} = {self._override_description}"

        parts = self._build_formula_parts()
        formula = " ".join(parts)
        return f"{self.total} = {formula}"

    def _build_formula_parts(self) -> List[str]:
        """Build the formula parts for string representation."""
        parts = []

        # Add dice results
        for i, result in enumerate(self.results):
            result_str = str(result)
            result_total = (sum(result.kept) * result.multiply) // result.divide

            if i == 0:
                # Handle special negative dice formatting
                if (
                    hasattr(self, "_has_leading_zero_minus")
                    and self._has_leading_zero_minus
                    and result_total < 0
                ):
                    if result_str.startswith("-"):
                        parts.append(f"0 - {result_str[1:]}")
                    else:
                        parts.append(result_str)
                else:
                    parts.append(result_str)
            else:
                # Format subsequent results with appropriate operators
                if result_total < 0:
                    parts.append(
                        f"- {result_str[1:]}"
                    )  # Remove negative and add our own
                else:
                    parts.append(f"+ {result_str}")

        # Add modifiers
        for modifier in self.modifiers:
            parts.append(str(modifier))

        return parts


class Dice:
    """Main dice rolling class with support for complex expressions
    and various dice systems."""

    _dice_re = re.compile(
        r"""(?P<num>\d+)d(?P<sides>\d+|F|%)              # NdM or NdF
            (?P<keep_ops>(?:\s*k[hl]\s*\d*)*)?           # optional multiple
            (?P<drop_ops>(?:\s*d[hl]\s*\d*)*)?           # optional multiple
            (?:\s*x\s*(?P<multiply>\d+)(?!d))?           # optional xN
            (?:\s*/\s*(?P<divide>\d+)(?!d))?             # optional /N
            (?:r(?P<reroll_count>\d*|o)                  # optional rN or r
               (?P<reroll_cmp><=|>=|<|>|=)              # comparison
               (?P<reroll_target>\d+)                   # target
            )?
            (?:e(?:(?P<explode_cmp><=|>=|<|>|=)(?P<explode_target>\d+)|
               (?P<explode_simple>\d+))?)?  # optional exploding dice
            """,
        re.IGNORECASE | re.VERBOSE,
    )
    _mod_re = re.compile(r"([+-]\s*\d+)(?!d)")

    _cmp_funcs: Dict[str, Callable[[int, int], bool]] = COMPARISON_OPERATORS

    @classmethod
    def _roll_original_method(
        cls, expr: str, modifiers: Optional[Dict[str, Union[int, str]]] = None
    ) -> RollResultSet:
        """Roll dice using the original parsing method for backward
        compatibility."""
        from .debug_logger import get_debug_logger

        logger = get_debug_logger()

        logger.log_step("ORIGINAL_PARSER", "Using original parsing method")

        # Input validation
        DiceExpressionValidator.validate_expression_input(expr)

        # Normalize the expression
        expr = ExpressionProcessor.normalize_unicode(expr)

        # Handle shorthand expressions
        expr = ExpressionProcessor.process_shorthands(expr)

        # Handle negative dice expressions (convert "-XdY" to "0 - XdY")
        expr = ExpressionProcessor.process_negative_dice(expr)

        # Handle special flux cases
        if "GOODFLUX_SPECIAL" in expr:
            logger.log_step("SPECIAL_CASE", "Handling GOODFLUX")
            return cls._handle_goodflux_roll()
        elif "BADFLUX_SPECIAL" in expr:
            logger.log_step("SPECIAL_CASE", "Handling BADFLUX")
            return cls._handle_badflux_roll()

        results: List[RollResult] = []

        logger.log_step("DICE_MATCHING", f"Finding dice expressions in: '{expr}'")

        # Find all dice expressions and their positions
        dice_matches = list(cls._dice_re.finditer(expr))

        logger.log(f"Found {len(dice_matches)} dice expressions")

        # Validate that we found at least some dice expressions
        if not dice_matches:
            error_msg = (
                "No valid dice expressions found in: "
                if "d" not in expr.lower()
                else "No valid dice expressions found in: "
            )
            raise ParseError(f"{error_msg}{expr}")

        # Check if we have cross-dice operations like "1d6 + 2d8"
        cross_dice_operations = ["+", "-"]
        cross_dice_op = None

        # Only check for cross-dice operations if we have multiple dice
        # expressions
        if len(dice_matches) >= 2:
            for op in cross_dice_operations:
                if op in expr:
                    cross_dice_op = op
                    break

        if cross_dice_op and len(dice_matches) >= 2:
            logger.log_step(
                "CROSS_DICE",
                f"Detected cross-dice operations with '{cross_dice_op}'",
            )
            # Handle cross-dice operations (e.g., "1d6 + 2d8")
            for match in dice_matches:
                dice_result = cls._roll_single_dice_expression(expr, match)
                results.append(dice_result)
        else:
            # Handle normal single or multiple dice of same type
            for match in dice_matches:
                dice_result = cls._roll_single_dice_expression(expr, match)
                results.append(dice_result)

        # Create modifiers list
        mods = []
        if modifiers:
            for name, value in modifiers.items():
                mod = RollModifier(value, name)
                mods.append(mod)

        result_set = RollResultSet(results, mods, cls)

        # Handle special display cases
        if "GOODFLUX_SPECIAL" in expr:
            # This shouldn't happen here since we handle it earlier, but just
            # in case
            pass
        elif "BADFLUX_SPECIAL" in expr:
            # This shouldn't happen here since we handle it earlier, but just
            # in case
            pass

        return result_set

    @classmethod
    def _roll_single_dice_expression(cls, expr: str, match) -> RollResult:
        """Roll a single dice expression given a regex match."""
        num = int(match.group("num"))
        sides_str = match.group("sides")

        # Normalize Unicode characters in sides string for display
        normalized_sides_str = ExpressionLexer.normalize_unicode_chars(sides_str)

        is_fudge = sides_str.upper() == "F"
        is_percentile = sides_str == "%"
        sides = 6 if is_fudge else (100 if is_percentile else int(normalized_sides_str))

        # reroll parameters
        rc_str = match.group("reroll_count")
        reroll_cmp = match.group("reroll_cmp")
        target = (
            int(match.group("reroll_target")) if match.group("reroll_target") else None
        )
        max_rerolls = (
            None
            if rc_str == ""
            else (1 if rc_str == "o" else (int(rc_str) if rc_str else None))
        )

        # exploding dice parameters
        explode_cmp = match.group("explode_cmp")
        explode_target_str = match.group("explode_target")
        explode_simple_str = match.group("explode_simple")
        explode_target = None

        if explode_target_str is not None:
            explode_target = int(explode_target_str)
        elif explode_simple_str is not None:
            explode_target = int(explode_simple_str)
            explode_cmp = None  # Simple target, no comparison
        elif match.group(0).find("e") != -1:  # 'e' is present but no number
            explode_target = sides  # Default to maximum value
            explode_cmp = None

        # Validate that fudge dice cannot be used with reroll operations
        if is_fudge and reroll_cmp and target is not None:
            error = ParseError("Reroll is not supported for fudge dice")
            error.condition_type = "reroll"
            raise error

        # Validate infinite conditions before rolling
        if not is_fudge and not is_percentile and reroll_cmp and target is not None:
            DiceExpressionValidator.validate_reroll_condition(
                sides, reroll_cmp, target, expr
            )

        if (
            not is_fudge
            and not is_percentile
            and explode_target is not None
            and explode_cmp is not None
        ):
            DiceExpressionValidator.validate_explosion_condition(
                sides, explode_cmp, explode_target, expr
            )

        rolls: List[int] = []
        all_rolls: List[int] = []
        for _ in range(num):
            count = 0
            if is_fudge:
                raw_value, value = DiceRoller.roll_fudge_die()
                all_rolls.append(raw_value)  # Store raw value for display
            elif is_percentile:
                value, tens_roll, ones_roll = DiceRoller.roll_percentile_die()
                # Store both dice for display
                all_rolls.append((tens_roll, ones_roll))
            else:
                value = DiceRoller.roll_standard_die(sides)
                all_rolls.append(value)

            # apply rerolls (not applicable to fudge or percentile dice)
            if not is_fudge and not is_percentile and reroll_cmp and target is not None:
                while DiceRoller.should_reroll(
                    value, reroll_cmp, target, cls._cmp_funcs
                ) and (max_rerolls is None or count < max_rerolls):
                    count += 1
                    value = DiceRoller.roll_standard_die(sides)
                    all_rolls.append(value)
            elif is_percentile and reroll_cmp and target is not None:
                while DiceRoller.should_reroll(
                    value, reroll_cmp, target, cls._cmp_funcs
                ) and (max_rerolls is None or count < max_rerolls):
                    count += 1
                    value, tens_roll, ones_roll = DiceRoller.roll_percentile_die()
                    all_rolls.append((tens_roll, ones_roll))

            # Handle exploding dice (not applicable to fudge or percentile
            # dice)
            current_total = value
            if not is_fudge and not is_percentile and explode_target is not None:
                while True:
                    if DiceRoller.should_explode(
                        value, explode_cmp, explode_target, cls._cmp_funcs
                    ):
                        value = DiceRoller.roll_standard_die(sides)
                        all_rolls.append(value)
                        current_total += value
                    else:
                        break

            rolls.append(current_total)

        # Parse multiple keep operations
        keep_ops_str = match.group("keep_ops") or ""
        keep_operations = KeepOperationsParser.parse_keep_operations(keep_ops_str)

        # Parse multiple drop operations
        drop_ops_str = match.group("drop_ops") or ""
        drop_operations = DropOperationsParser.parse_drop_operations(drop_ops_str)

        # Debug logging for keep/drop operations
        from .debug_logger import get_debug_logger

        logger = get_debug_logger()
        if keep_operations:
            logger.log_step(
                "KEEP_OPERATIONS", f"Parsed keep operations: {keep_operations}"
            )
        if drop_operations:
            logger.log_step(
                "DROP_OPERATIONS", f"Parsed drop operations: {drop_operations}"
            )

        # For backward compatibility, still set legacy keep_type and keep_n
        if keep_operations:
            keep_type = keep_operations[0][0]  # First operation's type
            keep_n = keep_operations[0][1]  # First operation's count
        else:
            keep_type = None
            keep_n = None

        multiply = int(match.group("multiply")) if match.group("multiply") else 1
        divide = int(match.group("divide")) if match.group("divide") else 1

        return RollResult(
            num,
            normalized_sides_str,
            rolls,
            keep_type,
            keep_n,
            rc_str,
            reroll_cmp,
            target,
            all_rolls,
            multiply,
            divide,
            explode_target,
            explode_cmp,
            is_fudge=is_fudge,
            is_percentile=is_percentile,
            keep_operations=keep_operations,
            drop_operations=drop_operations,
        )

    @classmethod
    def _roll_single_dice_expression_from_string(cls, dice_expr: str) -> RollResult:
        """Roll a single dice expression from a string like '2d6kh1'."""
        # Validate the dice expression for common issues
        DiceExpressionValidator.validate_expression_input(dice_expr)

        # Use the existing regex to parse the dice expression
        match = cls._dice_re.match(dice_expr)
        if not match:
            raise ValueError(f"Invalid dice expression: {dice_expr}")
        return cls._roll_single_dice_expression(dice_expr, match)

    @classmethod
    def roll_with_precedence(
        cls, expr: str, modifiers: Optional[Dict[str, Union[int, str]]] = None
    ) -> "RollResultSet":
        """Roll dice with proper mathematical precedence parsing.

        This method automatically determines whether to use the new precedence
        parser or fall back to the original method based on expression
        complexity.
        """
        from .debug_logger import get_debug_logger

        logger = get_debug_logger()

        logger.log_step("PROCESSING", "Starting expression processing")

        # Normalize Unicode characters first
        expr = ExpressionProcessor.normalize_unicode(expr)
        logger.log_expression("NORMALIZED", expr)

        # Process shorthands first
        original_expr = expr
        expr = ExpressionProcessor.process_shorthands(expr)
        if expr != original_expr:
            logger.log_step("SHORTHAND_EXPANSION", f"'{original_expr}' -> '{expr}'")

        # Handle special flux cases
        if "GOODFLUX_SPECIAL" in expr:
            logger.log_step("SPECIAL_CASE", "Handling GOODFLUX")
            return cls._handle_goodflux_roll()
        elif "BADFLUX_SPECIAL" in expr:
            logger.log_step("SPECIAL_CASE", "Handling BADFLUX")
            return cls._handle_badflux_roll()

        # Check if we should use the new parser or fall back to original
        needs_precedence_parsing = ExpressionProcessor.should_use_precedence_parsing(
            expr
        )

        parser_type = "precedence" if needs_precedence_parsing else "original"
        logger.log_step("PARSER_SELECTION", f"Using {parser_type} parser")

        # If we don't need precedence parsing, use the simpler original method
        if not needs_precedence_parsing:
            return cls._roll_original_method(expr, modifiers)

        # Handle negative dice expressions for precedence parser
        expr = ExpressionProcessor.process_negative_dice(expr)

        # Validate input for both parser paths
        DiceExpressionValidator.validate_expression_input(expr)

        try:
            return cls._parse_with_precedence(expr, modifiers)
        except (SyntaxError, AttributeError, TypeError, ParseError) as e:
            logger.log_step(
                "FALLBACK",
                f"Parser error: {e}, falling back to original method",
            )
            # Fall back to the original parsing method only for parsing errors
            return cls._roll_original_method(expr, modifiers)

    @classmethod
    def roll(
        cls,
        expr: str,
        modifiers: Optional[Dict[str, Union[int, str]]] = None,
        debug: bool = False,
        logger=None,
    ) -> "RollResultSet":
        """Roll dice expressions with proper mathematical precedence.

        This is the main entry point for rolling dice. It automatically chooses
        the best parsing method based on the expression complexity.

        Args:
            expr: The dice expression to evaluate (e.g., "2d6 + 7 x 4 x 2")
            modifiers: Optional additional modifiers as a dictionary
            debug: Enable debug logging to see detailed parsing and rolling
                steps
            logger: Optional Python logger instance (from logging module) or
                StringLogger for testing

        Returns:
            RollResultSet with the evaluated results

        Examples:
            >>> Dice.roll("2d6")  # Simple dice roll
            >>> Dice.roll("2d6 + 7 x 4 x 2")  # Complex mathematical expression
            >>> Dice.roll("1d10 / 2 x 2 + 5")  # Proper precedence handling
            >>> Dice.roll("2d6", debug=True)  # With debug logging

            # With custom logger
            >>> import logging
            >>> logger = logging.getLogger('my_app')
            >>> Dice.roll("2d6", debug=True, logger=logger)

            # With string logger for testing/APIs
            >>> from wyrdbound_dice.debug_logger import StringLogger
            >>> string_logger = StringLogger()
            >>> Dice.roll("2d6", debug=True, logger=string_logger)
            >>> print(string_logger.get_logs())
        """
        from .debug_logger import get_debug_logger, set_debug_mode

        # Set debug mode for this roll
        set_debug_mode(debug, logger)
        debug_logger = get_debug_logger()

        debug_logger.log_step("START", f"Rolling expression: '{expr}'")
        if modifiers:
            debug_logger.log_step("MODIFIERS", f"Using modifiers: {modifiers}")

        result = cls.roll_with_precedence(expr, modifiers)

        debug_logger.log_step("COMPLETE", f"Final result: {result.total}")

        # Reset debug mode
        set_debug_mode(False)

        return result

    @classmethod
    def _handle_goodflux(cls, expr: str) -> str:
        """GOODFLUX: Roll 2d6, subtract lower from higher."""
        # We'll handle this as a special case in the roll method
        return "GOODFLUX_SPECIAL"

    @classmethod
    def _handle_badflux(cls, expr: str) -> str:
        """BADFLUX: Roll 2d6, subtract higher from lower."""
        # We'll handle this as a special case in the roll method
        return "BADFLUX_SPECIAL"

    @classmethod
    def _handle_goodflux_roll(cls) -> RollResultSet:
        """Handle GOODFLUX: Roll 2d6, subtract lower from higher."""
        return FluxDiceHandler.roll_flux(True)

    @classmethod
    def _handle_badflux_roll(cls) -> RollResultSet:
        """Handle BADFLUX: Roll 2d6, subtract higher from lower."""
        return FluxDiceHandler.roll_flux(False)

    @classmethod
    def _parse_with_precedence(
        cls, expr: str, modifiers: Optional[Dict[str, Union[int, str]]]
    ) -> "RollResultSet":
        """Parse expression using the precedence parser."""
        from .debug_logger import get_debug_logger

        logger = get_debug_logger()

        logger.log_step("TOKENIZING", f"Tokenizing expression: '{expr}'")

        # Tokenize the expression
        lexer = ExpressionLexer(expr)
        tokens = []
        while True:
            token = lexer.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break

        logger.log_tokens(tokens[:-1])  # Exclude EOF token for cleaner output

        logger.log_step("PARSING", "Parsing tokens with precedence rules")

        # Parse with proper precedence
        parser = ExpressionParser(tokens)
        parsed_expr = parser.parse()

        logger.log_step("EVALUATING", "Evaluating parsed expression")

        # Evaluate the expression
        result = parsed_expr.evaluate(cls)

        logger.log_step("RESULT", f"Expression evaluated to: {result.value}")

        # Create modifiers list
        mods = []
        if modifiers:
            logger.log_step("MODIFIERS", f"Processing {len(modifiers)} modifiers")
            for name, value in modifiers.items():
                mod = RollModifier(value, name)
                mods.append(mod)
                logger.log(f"Added modifier '{name}': {mod.value}")

        # Create a custom result set that shows the full mathematical
        # expression
        result_set = RollResultSet(result.dice_results, mods, cls)

        # Override the total calculation to use our evaluated result plus
        # modifiers
        modifier_total = sum(mod.value for mod in mods)
        final_total = result.value + modifier_total
        result_set._override_total = final_total

        logger.log_calculation(
            "TOTAL",
            [result.value, f"modifiers({modifier_total})"],
            final_total,
        )

        # Build description that includes modifiers
        if mods:
            modifier_strs = [str(mod) for mod in mods]
            result_set._override_description = (
                result.description + " " + " ".join(modifier_strs)
            )
        else:
            result_set._override_description = result.description

        return result_set


class KeepOperationsParser:
    """Handles parsing of keep operations from dice expressions."""

    @staticmethod
    def parse_keep_operations(keep_ops_str: str) -> List[Tuple[str, int]]:
        """Parse multiple keep operations from a string like 'kh2kl1'.

        Args:
            keep_ops_str: String containing keep operations (e.g., 'kh2kl1',
            'klkh3', ' kh 3')

        Returns:
            List of tuples containing (keep_type, keep_n) for each operation
        """
        if not keep_ops_str:
            return []

        # Pattern to match individual keep operations - handle spaces around
        # numbers
        keep_pattern = re.compile(r"k([hl])\s*(\d*)", re.IGNORECASE)
        operations = []

        for match in keep_pattern.finditer(keep_ops_str):
            keep_type = match.group(1).lower()
            keep_n_str = match.group(2).strip() if match.group(2) else ""
            keep_n = int(keep_n_str) if keep_n_str else DEFAULT_KEEP_COUNT

            # Validate keep_n is not negative
            if keep_n < 0:
                raise ValueError(f"Keep count cannot be negative: k{keep_type}{keep_n}")

            operations.append((keep_type, keep_n))

        return operations


class DropOperationsParser:
    """Handles parsing of drop operations from dice expressions."""

    @staticmethod
    def parse_drop_operations(drop_ops_str: str) -> List[Tuple[str, int]]:
        """Parse multiple drop operations from a string like 'dh2dl1'.

        Args:
            drop_ops_str: String containing drop operations (e.g., 'dh2dl1',
            'dldh3', ' dh 3')

        Returns:
            List of tuples containing (drop_type, drop_n) for each operation
        """
        if not drop_ops_str:
            return []

        # Pattern to match individual drop operations - handle spaces around
        # numbers
        drop_pattern = re.compile(r"d([hl])\s*(\d*)", re.IGNORECASE)
        operations = []

        for match in drop_pattern.finditer(drop_ops_str):
            drop_type = match.group(1).lower()
            drop_n_str = match.group(2).strip() if match.group(2) else ""
            drop_n = int(drop_n_str) if drop_n_str else DEFAULT_KEEP_COUNT

            # Validate drop_n is not negative
            if drop_n < 0:
                raise ValueError(f"Drop count cannot be negative: d{drop_type}{drop_n}")

            operations.append((drop_type, drop_n))

        return operations


class GoodFluxResult(RollResult):
    """Special result class for GOODFLUX rolls."""

    def __init__(self, roll1: int, roll2: int, higher: int, lower: int):
        # Store the raw rolls in all_rolls
        all_rolls = [roll1, roll2]
        # The effective result is higher - lower
        rolls = [higher - lower]
        super().__init__(2, 6, rolls, None, None, all_rolls=all_rolls)
        self.roll1 = roll1
        self.roll2 = roll2
        self.higher = higher
        self.lower = lower

    def __str__(self):
        return (
            f"{self.higher} (1d6: {self.higher}) - "
            + f"{self.lower} (1d6: {self.lower})"
        )


class BadFluxResult(RollResult):
    """Special result class for BADFLUX rolls."""

    def __init__(self, roll1: int, roll2: int, higher: int, lower: int):
        # Store the raw rolls in all_rolls
        all_rolls = [roll1, roll2]
        # The effective result is lower - higher (negative)
        rolls = [lower - higher]
        super().__init__(2, 6, rolls, None, None, all_rolls=all_rolls)
        self.roll1 = roll1
        self.roll2 = roll2
        self.higher = higher
        self.lower = lower

    def __str__(self):
        return (
            f"{self.lower} (1d6: {self.lower}) - "
            + f"{self.higher} (1d6: {self.higher})"
        )


class FluxDiceHandler:
    """Handles special Flux dice rolling logic."""

    @staticmethod
    def create_flux_result(
        roll1: int, roll2: int, is_good_flux: bool
    ) -> "RollResultSet":
        """Create a flux result set from two d6 rolls."""
        higher = max(roll1, roll2)
        lower = min(roll1, roll2)

        if is_good_flux:
            result = GoodFluxResult(roll1, roll2, higher, lower)
        else:
            result = BadFluxResult(roll1, roll2, higher, lower)

        return RollResultSet([result])

    @staticmethod
    def roll_flux(is_good_flux: bool) -> "RollResultSet":
        """Roll flux dice and return the appropriate result."""
        roll1 = DiceRoller.roll_standard_die(6)
        roll2 = DiceRoller.roll_standard_die(6)
        return FluxDiceHandler.create_flux_result(roll1, roll2, is_good_flux)


class DiceExpressionValidator:
    """Handles validation of dice expressions and conditions."""

    @staticmethod
    def validate_expression_input(expr: str) -> None:
        """
        Validate dice expression input and raise ParseError for
        invalid syntax.
        """
        if not expr or expr.isspace():
            raise ParseError(f"Empty or whitespace-only expression: {repr(expr)}")

        # Check for any dice-like patterns
        if not re.search(r"\d*d\d*[fF%]?", expr):
            if re.match(r"^[\d\+\-\*\/\sx\×\÷\(\)\s]+$", expr):
                pass  # Valid mathematical expression without dice
            else:
                raise ParseError(f"No valid dice expression found: {expr}")

        # Check for malformed dice expressions
        validation_patterns = [
            (r"\bd\d*[fF%]?\b", r"\d+d\d*[fF%]?\b", "missing dice count"),
            (r"\d+d\s*$", None, "missing die sides"),
            (r"[\+\-\*\/x×÷]\s*$", None, "trailing operator without operand"),
            (r"^[\+\*\/x×÷]", None, "leading operator without operand"),
            (
                r"[\+\-\*\/x×÷][\s]*[\+\-\*\/x×÷]",
                None,
                "double operators not allowed",
            ),
            (
                r"\d+\.\d+d\d+|\d+d\d*\.\d+",
                None,
                "invalid decimal in dice expression",
            ),
            (r"\d+d0\b", None, "zero-sided dice not allowed"),
        ]

        for pattern, required_pattern, error_msg in validation_patterns:
            if re.search(pattern, expr):
                if required_pattern and not re.search(required_pattern, expr):
                    raise ParseError(f"Malformed dice expression - {error_msg}: {expr}")
                elif not required_pattern:
                    raise ParseError(f"{error_msg.capitalize()}: {expr}")

        # Check for multiple explode conditions
        dice_patterns = re.findall(r"\d+d\d*[fF]?[krleh\d<>=]*", expr)
        for dice_pattern in dice_patterns:
            if dice_pattern.count("e") > 1:
                raise ParseError(
                    "Multiple explode conditions not allowed in dice "
                    + f"expression: {dice_pattern}"
                )

    @staticmethod
    def check_infinite_condition(
        condition_type: str, sides: int, cmp: str, target: int, expression: str
    ) -> None:
        """
        Check if a condition would cause infinite loops and raise
        appropriate error.
        """
        error_conditions = {
            "<=": target >= sides,
            ">=": target <= 1,
            "<": target > sides,
            ">": target < 1,
            "=": sides == 1 and target == 1,
        }

        if error_conditions.get(cmp, False):
            range_desc = f"1-{sides}" if sides > 1 else "1"
            raise InfiniteConditionError(
                condition_type,
                expression,
                f"condition '{cmp} {target}' matches all "
                + f"possible rolls ({range_desc})",
            )

    @staticmethod
    def validate_reroll_condition(
        sides: int, reroll_cmp: str, reroll_target: int, expression: str
    ) -> None:
        """Validate that a reroll condition won't create an infinite loop."""
        DiceExpressionValidator.check_infinite_condition(
            "reroll", sides, reroll_cmp, reroll_target, expression
        )

    @staticmethod
    def validate_explosion_condition(
        sides: int, explode_cmp: str, explode_target: int, expression: str
    ) -> None:
        """
        Validate that an explosion condition won't create an infinite loop.
        """
        if explode_cmp is None:
            return  # Simple equality check is usually safe
        DiceExpressionValidator.check_infinite_condition(
            "explosion", sides, explode_cmp, explode_target, expression
        )


class DiceRoller:
    """Handles the actual rolling of individual dice."""

    @staticmethod
    def roll_fudge_die() -> Tuple[int, int]:
        """Roll a fudge die and return (display_value, effective_value)."""
        from .debug_logger import get_debug_logger

        raw_value = random.randint(1, 6)
        if raw_value <= FUDGE_NEGATIVE_MAX:
            effective_value = -1
        elif raw_value <= FUDGE_BLANK_MAX:
            effective_value = 0
        else:
            effective_value = 1

        logger = get_debug_logger()
        logger.log_roll("1dF", f"{effective_value} (raw: {raw_value})")

        return raw_value, effective_value

    @staticmethod
    def roll_standard_die(sides: int) -> int:
        """Roll a standard die with given number of sides."""
        from .debug_logger import get_debug_logger

        result = random.randint(1, sides)
        logger = get_debug_logger()
        logger.log_roll(f"1d{sides}", result)
        return result

    @staticmethod
    def roll_percentile_die() -> Tuple[int, int, int]:
        """
        Roll percentile dice and return (total_value, tens_die, ones_die).
        """
        from .debug_logger import get_debug_logger

        tens_die = random.randint(0, 9) * 10  # 0, 10, 20, ..., 90
        ones_die = random.randint(0, 9)  # 0, 1, 2, ..., 9
        total = tens_die + ones_die
        # Handle the special case where 00 + 0 = 100 (not 0)
        if total == 0:
            total = 100
        logger = get_debug_logger()
        logger.log_roll("1d%", f"{total} (tens: {tens_die}, ones: {ones_die})")
        return total, tens_die, ones_die

    @staticmethod
    def should_reroll(
        value: int,
        reroll_cmp: str,
        target: int,
        cmp_funcs: Dict[str, Callable],
    ) -> bool:
        """Check if a die should be rerolled based on the condition."""
        if not reroll_cmp or target is None:
            return False
        return cmp_funcs[reroll_cmp](value, target)

    @staticmethod
    def should_explode(
        value: int,
        explode_cmp: str,
        explode_target: int,
        cmp_funcs: Dict[str, Callable],
    ) -> bool:
        """Check if a die should explode based on the condition."""
        if explode_target is None:
            return False
        if explode_cmp:
            return cmp_funcs[explode_cmp](value, explode_target)
        else:
            return value == explode_target


class ExpressionProcessor:
    """Handles expression processing and normalization."""

    @staticmethod
    def normalize_unicode(expr: str) -> str:
        """Normalize unicode characters and symbols in the expression."""
        from .expression_lexer import ExpressionLexer

        return ExpressionLexer.normalize_unicode_chars(expr)

    @staticmethod
    def process_shorthands(expr: str) -> str:
        """
        Process shorthand dice expressions and convert them to
        standard notation.
        """
        expr_upper = expr.upper()

        # Check for special flux expressions first
        if "GOODFLUX" in expr_upper:
            return "GOODFLUX_SPECIAL"
        elif "BADFLUX" in expr_upper:
            return "BADFLUX_SPECIAL"

        # Replace standard shorthands with their expanded forms
        for shorthand, expansion in SHORTHAND_EXPANSIONS.items():
            if shorthand in expr_upper:
                expr = expr_upper.replace(shorthand, expansion)

        return expr

    @staticmethod
    def process_negative_dice(expr: str) -> str:
        """
        Process negative dice expressions and convert them to '0 - XdY'
        format.
        """
        # Pattern to match negative dice expressions at start of string or
        # after operators/parentheses
        negative_dice_pattern = re.compile(
            r"(^|[\+\-\*\/\(\s])\s*-(\d+d(?:\d+|F)[^\s\+\-\*\/\)]*)",
            re.IGNORECASE,
        )

        def replace_negative_dice(match):
            prefix = match.group(1)
            dice_expr = match.group(2)  # The dice expression without the minus

            # If the prefix is already a minus, don't double-convert
            if prefix.strip() == "-":
                return match.group(0)  # Return original match

            # Convert -XdY to prefix + 0 - XdY
            if prefix.strip() == "":
                return f"0 - {dice_expr}"
            else:
                return f"{prefix} 0 - {dice_expr}"

        return negative_dice_pattern.sub(replace_negative_dice, expr)

    @staticmethod
    def should_use_precedence_parsing(expr: str) -> bool:
        """Determine if expression needs precedence parsing."""
        has_mult_div = any(op in expr for op in ["x", "*", "×", "/"])
        has_add_sub_with_numbers = any(op in expr for op in ["+", "-"]) and any(
            char.isdigit() for char in expr.replace("d", "")
        )
        return has_mult_div or has_add_sub_with_numbers
