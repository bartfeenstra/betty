"""
System integration.
"""

from __future__ import annotations

from enum import IntEnum
from typing import final


@final
class ExitCode(IntEnum):
    """
    Betty's system exit codes.
    """

    OK = 0

    # User-caused exits are numbered 1-9.
    USER_QUIT = 1

    # Error-caused exits are numbered 11-19.
    ERROR_UNEXPECTED_UNRECOVERABLE = 11
    ERROR_UNEXPECTED_RECOVERABLE = 12
    ERROR_USAGE = 13
