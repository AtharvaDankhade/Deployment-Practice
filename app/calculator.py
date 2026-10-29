"""Pure calculator logic.

No I/O, no framework imports: this module is trivial to unit test and is shared
by both the CLI (calculator.py) and the HTTP API (app/main.py).
"""

from __future__ import annotations

import math

Number = float | int


class CalculatorError(ValueError):
    """Raised when an operation cannot be performed."""


def add(a: Number, b: Number) -> float:
    return a + b


def subtract(a: Number, b: Number) -> float:
    return a - b


def multiply(a: Number, b: Number) -> float:
    return a * b


def divide(a: Number, b: Number) -> float:
    if b == 0:
        raise CalculatorError("Cannot divide by zero")
    return a / b


OPERATIONS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
}

SYMBOLS = {
    "add": "+",
    "subtract": "-",
    "multiply": "*",
    "divide": "/",
}


def calculate(operation: str, a: Number, b: Number) -> float:
    """Apply ``operation`` to ``a`` and ``b`` and return the result."""
    try:
        func = OPERATIONS[operation]
    except KeyError:
        raise CalculatorError(f"Unknown operation: {operation!r}") from None

    result = float(func(a, b))
    if not math.isfinite(result):
        raise CalculatorError("Result is not a finite number")
    return result


def format_result(value: float) -> str:
    """Render 12.0 as '12' and 12.5 as '12.5'."""
    return str(int(value)) if value == int(value) else str(value)
