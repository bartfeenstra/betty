"""
Argparse utilities.
"""

from __future__ import annotations

import argparse as stdargparse
from typing import TYPE_CHECKING, Final, final

from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.user.error import UserFacingError
from betty.validation import Invalid

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.localizer import Localizer
    from betty.validation import Validator


@final
class UserFacingArgumentError(UserFacingError, stdargparse.ArgumentError):
    """
    A user-facing argparse argument error.

    This can be raised by argument type callbacks. The console catches these errors, and renders them with rich markup.
    """

    def __init__(self, error: UserFacingError, /):
        super().__init__(error, None, "")
        self.error: Final[UserFacingError] = error


def validator_to_argument_type[T](
    validator: Validator[str, T], /
) -> Callable[[str], T]:
    """
    Convert a validator to an argparse argument type.
    """

    def _validator_to_argument_type(value: str, /) -> T:
        try:
            return validator(value)
        except Invalid as error:
            raise UserFacingArgumentError(error) from error

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
