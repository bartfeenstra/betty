"""
Provide string handling utilities.
"""

import re
from typing import Final

_camel_case_pattern: Final[re.Pattern[str]] = re.compile(r"(?<!^)(?=[A-Z])")


def camel_case_to_snake_case(string: str, /) -> str:
    """
    Convert camel case to snake case.
    """
    return _camel_case_pattern.sub("_", string).lower()


def camel_case_to_kebab_case(string: str, /) -> str:
    """
    Convert camel case to kebab case.
    """
    return _camel_case_pattern.sub("-", string).lower()


def upper_camel_case_to_lower_camel_case(string: str, /) -> str:
    """
    Convert upper camel case to lower camel case.
    """
    if not string:
        return string
    return string[0].lower() + string[1:]


def snake_case_to_kebab_case(string: str, /) -> str:
    """
    Convert snake case to kebab case.
    """
    return string.replace("_", "-")


def snake_case_to_upper_camel_case(string: str, /) -> str:
    """
    Convert snake case to upper camel case.
    """
    return "".join(
        substring[0].upper() + substring[1:] if substring else ""
        for substring in string.split("_")
    )


def snake_case_to_lower_camel_case(string: str, /) -> str:
    """
    Convert snake case to lower camel case.
    """
    string = snake_case_to_upper_camel_case(string)
    return string[0].lower() + string[1:] if string else ""


def kebab_case_to_snake_case(string: str, /) -> str:
    """
    Convert kebab case to snake case.
    """
    return string.replace("-", "_")


def kebab_case_to_lower_camel_case(string: str, /) -> str:
    """
    Convert kebab case to lower camel case.
    """
    return upper_camel_case_to_lower_camel_case(
        "".join(
            substring[0].upper() + substring[1:] if substring else ""
            for substring in string.split("-")
        )
    )
