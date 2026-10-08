"""
An API to interact with Betty's user.
"""

from __future__ import annotations

from enum import IntEnum
from typing import final


@final
class Severity(IntEnum):
    """
    User communication severities.
    """

    ERROR = 1
    """
    Something went wrong and was aborted.
    """

    WARN = 2
    """
    Something may have gone wrong, or has gone wrong and Betty has recovered from it.
    """

    CONFIRM = 3
    """
    Confirm a user action.
    """

    INFO = 4
    """
    Provide additional, non-essential, related information.
    """

    DEBUG = 5
    """
    Details relevant to debugging.
    """
