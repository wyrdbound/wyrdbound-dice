"""Debug logging utilities for wyrdbound_dice."""

import logging
import sys
from typing import Any, Optional


class DebugLogger:
    """A debug logger that can use Python's standard logging interface."""

    def __init__(self, enabled: bool = False, logger: Optional[logging.Logger] = None):
        self.enabled = enabled
        if logger is None:
            # Create a default logger that outputs to stdout
            self.logger = logging.getLogger("wyrdbound_dice.debug")
            # Clear any existing handlers to avoid duplication
            self.logger.handlers.clear()
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)
            # Prevent propagation to avoid duplicate messages
            self.logger.propagate = False
        else:
            self.logger = logger

    def set_logger(self, logger: logging.Logger) -> None:
        """Set a custom logger backend."""
        self.logger = logger

    def log(self, message: str, *args: Any) -> None:
        """Log a debug message if debugging is enabled."""
        if self.enabled:
            formatted_message = message.format(*args) if args else message
            self.logger.debug(f"DEBUG: {formatted_message}")

    def log_step(self, step: str, description: str) -> None:
        """Log a processing step with standardized formatting."""
        if self.enabled:
            self.logger.debug(f"DEBUG: [{step}] {description}")

    def log_expression(self, label: str, expression: str) -> None:
        """Log an expression with a label."""
        if self.enabled:
            self.logger.debug(f"DEBUG: {label}: '{expression}'")

    def log_tokens(self, tokens: list) -> None:
        """Log tokenization results."""
        if self.enabled:
            token_strs = [str(token) for token in tokens]
            self.logger.debug(f"DEBUG: Tokens: {token_strs}")

    def log_roll(self, dice_type: str, result: Any) -> None:
        """Log individual dice roll results."""
        if self.enabled:
            self.logger.debug(f"DEBUG: Rolling {dice_type}: {result}")

    def log_calculation(self, operation: str, operands: list, result: Any) -> None:
        """Log calculation steps."""
        if self.enabled:
            operand_strs = [str(op) for op in operands]
            self.logger.debug(f"DEBUG: {operation} {' '.join(operand_strs)} = {result}")


class StringLogger:
    """A logger that captures messages to a string buffer for
    testing/API purposes.
    """

    def __init__(self):
        self.messages = []

    def debug(self, message: str) -> None:
        """Log a debug message to the string buffer."""
        self.messages.append(message)

    def info(self, message: str) -> None:
        """Log an info message to the string buffer."""
        self.messages.append(message)

    def warning(self, message: str) -> None:
        """Log a warning message to the string buffer."""
        self.messages.append(message)

    def error(self, message: str) -> None:
        """Log an error message to the string buffer."""
        self.messages.append(message)

    def get_logs(self) -> str:
        """Get all logged messages as a single string."""
        return "\n".join(self.messages)

    def clear(self) -> None:
        """Clear all logged messages."""
        self.messages.clear()


# Global debug logger instance
_debug_logger: Optional[DebugLogger] = None


def get_debug_logger() -> DebugLogger:
    """Get the global debug logger instance."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger(False)
    return _debug_logger


def set_debug_mode(enabled: bool, logger: Optional[logging.Logger] = None) -> None:
    """Enable or disable debug mode globally, optionally with a
    custom logger.
    """
    global _debug_logger
    _debug_logger = DebugLogger(enabled, logger)


def configure_debug_logger(logger: logging.Logger) -> None:
    """Configure the global debug logger to use a custom logger backend."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = DebugLogger(False, logger)
    else:
        _debug_logger.set_logger(logger)
