"""
Command Line Interface error handling.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator, TYPE_CHECKING

import click

from betty.error import UserFacingError
from betty.locale.localizer import DEFAULT_LOCALIZER

if TYPE_CHECKING:
    from betty.locale.localizer import Localizer


@contextmanager
def user_facing_error_to_bad_parameter(
    localizer: Localizer = DEFAULT_LOCALIZER,
) -> Iterator[None]:
    """
    Convert a :py:class:`betty.error.UserFacingError` exception to a :py:class:`click.BadParameter` exception.
    """
    try:
        yield
    except UserFacingError as error:
        message = error.localize(localizer)
        logging.getLogger(__name__).debug(message)
        raise click.BadParameter(message) from None
