"""
Integrate the console and assertion APIs.
"""

import argparse
from collections.abc import Callable
from typing import TypeVar

from betty.assertion import Assertion
from betty.exception import HumanFacingException
from betty.locale.localizer import Localizer

_T = TypeVar("_T")


def assertion_to_argument_type(
    assertion: Assertion[str, _T], *, localizer: Localizer
) -> Callable[[str], _T]:
    """
    Convert an assertion to an argparse argument type.
    """

    def _assertion_to_argument_type(value: str) -> _T:
        try:
            return assertion(value)
        except HumanFacingException as error:
            raise argparse.ArgumentTypeError(error.localize(localizer)) from error

    return _assertion_to_argument_type
