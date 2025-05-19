"""
Command Line Interface error handling.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

import asyncclick as click

from betty.exception import UserFacingException
from betty.locale.localizer import DEFAULT_LOCALIZER

if TYPE_CHECKING:
    from collections.abc import Iterator

    from betty.locale.localizer import Localizer


@contextmanager
def user_facing_exception_to_bad_parameter(
    localizer: Localizer = DEFAULT_LOCALIZER,
) -> Iterator[None]:
    """
    Convert a :py:class:`betty.exception.UserFacingException` exception to a :py:class:`asyncclick.BadParameter` exception.
    """
    try:
        yield
    except UserFacingException as error:
        message = error.localize(localizer)
        logging.getLogger(__name__).debug(message)
        raise click.BadParameter(message) from None
