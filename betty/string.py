import re

_CAMEL_CASE_PATTERN = re.compile(r'(?<!^)(?=[A-Z])')


def camel_case_to_snake_case(string: str) -> str:
    """
    Convert camel case to snake case.
    """
    return _CAMEL_CASE_PATTERN.sub('_', string).lower()


def camel_case_to_kebab_case(string: str) -> str:
    """
    Convert camel case to kebab case.
    """
    return _CAMEL_CASE_PATTERN.sub('-', string).lower()


def upper_camel_case_to_lower_camel_case(string: str) -> str:
    """
    Convert upper camel case to lower camel case.
    """
    return string[0].lower() + string[1:]
