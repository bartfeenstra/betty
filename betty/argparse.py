"""
Integrate the console and assertion APIs.
"""

import argparse as stdargparse
from collections.abc import Callable

from betty.assertion import Assertion
from betty.exception import HumanFacingException
from betty.locale.localize import Localizer


def assertion_to_argument_type[T](
    assertion: Assertion[str, T], *, localizer: Localizer
) -> Callable[[str], T]:
    """
    Convert an assertion to an argparse argument type.
    """

    def _assertion_to_argument_type(value: str) -> T:
        try:
            return assertion(value)
        except HumanFacingException as error:
            raise stdargparse.ArgumentTypeError(error.localize(localizer)) from error

    return _assertion_to_argument_type
