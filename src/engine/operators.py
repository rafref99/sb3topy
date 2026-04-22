"""
operators.py

Contains functions primarily used by project.py to ensure maximum
compatibility.
"""

__all__ = [
    'tonum', 'toint', 'letter_of', 'pick_rand',
    'gt', 'lt', 'eq', 'div', 'sqrt'
]

import math
import random
from typing import Any, Union


def tonum(value: Any) -> Union[int, float]:
    """Attempt to cast a value to a number"""
    if isinstance(value, (int, float)):
        return value
    try:
        f_value = float(value)
        if f_value.is_integer():
            return int(f_value)
        if math.isnan(f_value):
            return 0
        return f_value
    except (ValueError, TypeError):
        return 0


def toint(value: Any) -> int:
    """Attempts to round a value to an int"""
    if isinstance(value, int):
        return value
    try:
        return round(float(value))
    except (ValueError, TypeError, OverflowError):
        return 0


def letter_of(text: str, index: int) -> str:
    """Gets a letter from string"""
    try:
        return text[index - 1]
    except IndexError:
        return ""


def pick_rand(number1: Union[int, float], number2: Union[int, float]) -> Union[int, float]:
    """Rand int or float depending on values"""
    number1, number2 = min(number1, number2), max(number1, number2)
    if isinstance(number1, float) or isinstance(number2, float):
        return random.random() * abs(number2 - number1) + number1
    return random.randint(int(number1), int(number2))


def gt(value1: Any, value2: Any) -> bool:  # pylint: disable=invalid-name
    """Either numerical or string comparison"""
    if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
        return value1 > value2
    try:
        return float(value1) > float(value2)
    except (ValueError, TypeError):
        return str(value1).lower() > str(value2).lower()


def lt(value1: Any, value2: Any) -> bool:  # pylint: disable=invalid-name
    """Either numerical or string comparison"""
    if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
        return value1 < value2
    try:
        return float(value1) < float(value2)
    except (ValueError, TypeError):
        return str(value1).lower() < str(value2).lower()


def eq(value1: Any, value2: Any) -> bool:  # pylint: disable=invalid-name
    """Either numerical or string comparison"""
    if value1 == value2:
        return True
    try:
        return float(value1) == float(value2)
    except (ValueError, TypeError):
        return str(value1).lower() == str(value2).lower()


def div(value1: Any, value2: Any) -> Union[int, float]:
    """Divide handling division by zero"""
    try:
        return tonum(value1) / tonum(value2)
    except ZeroDivisionError:
        return float('infinity')


def sqrt(value: Union[int, float]) -> float:
    """Gets the square root handling negative values"""
    try:
        return math.sqrt(value)
    except (ValueError, TypeError):
        return float('nan')
