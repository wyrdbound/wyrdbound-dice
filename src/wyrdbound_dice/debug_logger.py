"""Debug logging utilities for wyrdbound_dice."""

import logging
import sys
import threading
from typing import Any, Optional


def _sanitize(text: Any) -> str:
    """Flatten newlines and carriage returns in text bound for a log line.

    Debug output is line-oriented and includes the caller's expression
    verbatim, so an expression containing a newline could forge an entire log
    record - ``1d6\nDEBUG: [COMPLETE] Final result: 999999`` produced exactly
    that line. Escaping them keeps one logical record on one line.
    """
    result = text if isinstance(text, str) else str(text)
    if "\n" in result or "\r" in result:
        result = result.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")
    return result


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
            self.logger.debug(f"DEBUG: {_sanitize(formatted_message)}")

    def log_step(self, step: str, description: str) -> None:
        """Log a processing step with standardized formatting."""
        if self.enabled:
            self.logger.debug(f"DEBUG: [{_sanitize(step)}] {_sanitize(description)}")

    def log_expression(self, label: str, expression: str) -> None:
        """Log an expression with a label."""
        if self.enabled:
            self.logger.debug(f"DEBUG: {_sanitize(label)}: '{_sanitize(expression)}'")

    def log_tokens(self, tokens: list) -> None:
        """Log tokenization results."""
        if self.enabled:
            token_strs = [_sanitize(token) for token in tokens]
            self.logger.debug(f"DEBUG: Tokens: {token_strs}")

    def log_roll(self, dice_type: str, result: Any) -> None:
        """Log individual dice roll results."""
        if self.enabled:
            self.logger.debug(
                f"DEBUG: Rolling {_sanitize(dice_type)}: {_sanitize(result)}"
            )

    def log_calculation(self, operation: str, operands: list, result: Any) -> None:
        """Log calculation steps."""
        if self.enabled:
            operand_strs = [_sanitize(op) for op in operands]
            self.logger.debug(
                f"DEBUG: {_sanitize(operation)} {' '.join(operand_strs)} "
                f"= {_sanitize(result)}"
            )


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


# Debug state is per-thread. It used to be one module global, which meant two
# concurrent rolls shared one logger: whichever finished first replaced it, and
# the other thread's remaining output went to a logger nobody was reading. Rolls
# on different threads are independent, so their debug state is too.
_state = threading.local()


def _current() -> DebugLogger:
    """Return this thread's debug logger, creating a disabled one if needed."""
    logger = getattr(_state, "debug_logger", None)
    if logger is None:
        logger = DebugLogger(False)
        _state.debug_logger = logger
    return logger


def get_debug_logger() -> DebugLogger:
    """Get the debug logger for the current thread."""
    return _current()


def set_debug_mode(enabled: bool, logger: Optional[logging.Logger] = None) -> None:
    """Enable or disable debug mode for the current thread.

    Args:
        enabled: Whether debug output is emitted.
        logger: Optional logger backend; a default stdout logger is used when
            omitted.
    """
    _state.debug_logger = DebugLogger(enabled, logger)


def swap_debug_logger(logger: DebugLogger) -> DebugLogger:
    """Install ``logger`` for this thread and return the one it replaced.

    Callers that enable debug for the duration of an operation use this to put
    the previous state back in a ``finally``, so an exception mid-roll cannot
    leave debug output enabled for everything that runs afterwards.
    """
    previous = _current()
    _state.debug_logger = logger
    return previous


def configure_debug_logger(logger: logging.Logger) -> None:
    """Point the current thread's debug logger at a custom backend."""
    _current().set_logger(logger)
