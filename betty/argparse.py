"""
Argparse utilities.
"""

from __future__ import annotations

import argparse as stdargparse
from typing import TYPE_CHECKING

from betty.localizables.gettext import _
from betty.localizables.markup import Lines, Paragraphs, Quote, UnorderedList
from betty.locator.operator import Operators
from betty.validation import Invalid

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.localizer import Localizer
    from betty.validation import Validator


def validator_to_argument_type[T](
    validator: Validator[str, T], /, *, localizer: Localizer
) -> Callable[[str], T]:
    """
    Convert a validator to an argparse argument type.
    """

    def _validator_to_argument_type(value: str) -> T:
        try:
            return validator(value)
        except* Invalid as errors:
            raise stdargparse.ArgumentTypeError(
                Paragraphs(
                    *(
                        Lines(
                            error.localizable_message,
                            UnorderedList(*[
                                operator.format()
                                for operator in Operators.reduce(
                                    *reversed(error.location)
                                )
                            ]),
                        )
                        for error in errors.exceptions
                        if isinstance(error, Invalid)
                    )
                ).localize(localizer)
            ) from None

    return _validator_to_argument_type


def add_yes_argument(
    parser: stdargparse.ArgumentParser, *, localizer: Localizer
) -> None:
    """
    Add an argument to skip any interactivity.
    """
    parser.add_argument(
        "-y",
        "--yes",
        dest="yes",
        default=False,
        action="store_true",
        help=_("Skip interactions and answer {yes} to all questions.")
        .format(yes=Quote("y"))
        .localize(localizer),
    )
