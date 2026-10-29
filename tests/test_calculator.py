"""Unit tests for the pure calculator core."""

import pytest

from app.calculator import CalculatorError, calculate, format_result


@pytest.mark.parametrize(
    ("operation", "a", "b", "expected"),
    [
        ("add", 2, 3, 5),
        ("add", -2, 2, 0),
        ("subtract", 10, 4, 6),
        ("multiply", 6, 7, 42),
        ("multiply", 2.5, 4, 10),
        ("divide", 9, 3, 3),
        ("divide", 1, 4, 0.25),
    ],
)
def test_calculate_ok(operation, a, b, expected):
    assert calculate(operation, a, b) == pytest.approx(expected)


def test_divide_by_zero_raises():
    with pytest.raises(CalculatorError, match="divide by zero"):
        calculate("divide", 1, 0)


def test_unknown_operation_raises():
    with pytest.raises(CalculatorError, match="Unknown operation"):
        calculate("modulo", 5, 2)


def test_non_finite_result_raises():
    with pytest.raises(CalculatorError, match="finite"):
        calculate("multiply", 1e308, 1e308)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(12.0, "12"), (12.5, "12.5"), (-0.0, "0")],
)
def test_format_result(value, expected):
    assert format_result(value) == expected
