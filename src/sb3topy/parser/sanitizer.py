"""
sanitizer.py

Contains functions which are useful for sanitization.

TODO Would repr() be a better way to quote strings?
"""

import logging
import math
import re
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


def clean_identifier(text: str, default: str = 'identifier') -> str:
    """Strips invalid character from an identifier"""
    # TODO Keep preluding underscores?
    cleaned = re.sub((
        r"(?a)(?:^([\d_]+))?"  # Preluding digits and _
        r"((?<!\\)%[sbn]|\W|__)*?"  # Other invalid characters
    ), "", text)

    if not cleaned:
        logger.warning("Stripped all characters from identifier '%s'", text)
        cleaned = default

    if not cleaned.isidentifier():
        logger.error("Failed to clean identifier '%s'", text)
        return "identifier"

    return cleaned


def quote_string(text: Any) -> str:
    """Double "quotes" text"""
    # Escape back slashes and double quotes
    text_str = re.sub(r'()(?=\\|")', r"\\", str(text))

    # Escape newlines
    text_str = '\\n'.join(text_str.splitlines())

    # Double quote the string
    return '"' + text_str + '"'


def quote_field(text: Any) -> str:
    """Single 'quotes' text"""
    # Escape back slashes and single quotes
    text_str = re.sub(r"()(?=\\|')", r"\\", str(text))

    # Escape newlines
    text_str = '\\n'.join(text_str.splitlines())

    # Single quote the string
    return "'" + text_str + "'"


def quote_number(text: Any) -> str:
    """
    Does not quote valid ints, but
    does quote everything else.

    Used to sanitize a value which may contain
    a large int which doesn't need quotes
    """
    text_str = str(text)
    try:
        if str(int(text_str)) == text_str:
            return text_str
        return quote_string(text)
    except ValueError:
        try:
            if str(float(text_str)) == text_str:
                int(float(text_str))
                return text_str
            return quote_string(text)
        except (ValueError, OverflowError):
            return quote_string(text)


def cast_number(value: Any, default: Union[int, float] = 0) -> Union[int, float]:
    """Casts a value to a number"""
    # Get number or return default
    try:
        num_value = float(value)

        if num_value.is_integer():
            return int(num_value)
        if math.isnan(num_value):
            return default

        return num_value

    except (ValueError, TypeError):
        try:
            return int(str(value), base=0)
        except (ValueError, TypeError):
            return default


def valid_md5ext(md5ext: str) -> bool:
    """Verifies a md5ext path is valid"""
    return re.fullmatch(r"[a-z0-9]{32}\.[a-z3]{3}", md5ext) is not None


def strip_pcodes(text: str) -> str:
    """Strips % format codes from a proccode"""
    return re.sub(
        r"(?<!\\)%[sbn]",
        "", text
    )


def cast_literal(value: Any, to_type: str) -> str:
    """
    Casts a value to a type
    Always returns a string
    """
    # Quote a string
    if to_type == "str":
        return quote_string(value)

    # Try to cast a float
    if to_type == "float":
        return str(cast_number(value))

    # Try to cast and round an int
    if to_type == "int":
        return str(round(cast_number(value)))

    # Get the bool value
    if to_type == "bool":
        return str(bool(value))

    # Get either a number or string
    if to_type == 'any':
        return str(quote_number(value))

    # Default behavior
    logger.warning("Unknown literal type '%s'", to_type)
    if value in (True, False, None):
        return str(value)
    return str(quote_number(value))


def cast_wrapper(value: str, from_type: str, to_type: str) -> str:
    """Puts a runtime cast wrapper around code"""

    # assert from_type in ('any', 'stack', 'int', 'float', 'str', 'bool', 'none')
    # assert to_type in ('any', 'stack', 'int', 'float', 'str', 'bool', 'none')

    # Don't cast any type
    if to_type == 'any':
        # logger.debug("Did not cast wrap '%s' to any", from_type)
        return value

    # Don't cast if both types are the same
    if to_type == from_type:
        # logger.debug("Did not cast wrap '%s' to '%s'", from_type, to_type)
        return value

    # Cast wrapper for strings
    if to_type == 'str':
        return "str(" + value + ")"

    # Cast wrapper for ints
    if to_type == 'int':
        # if from_type == 'float':
        #     return "round(" + value + ")"
        return "toint(" + value + ")"

    # Cast wrapper for floats
    if to_type == 'float':
        if from_type == 'int':
            return value
        return 'tonum(' + value + ")"

    # Handle blank stacks
    if to_type == 'stack' and from_type == 'none':
        return 'pass'

    # Handle blank bool inputs
    if to_type == 'bool' and from_type == 'none':
        return 'False'

    logger.warning("Unknown cast wrap for '%s' to '%s'", from_type, to_type)

    return value
