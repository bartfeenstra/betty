"""
Errors for the localizable API.
"""

from __future__ import annotations

from typing import final

from betty.locale.error import LocaleError


@final
class MissingPluralPlaceholder(LocaleError):
    """
    Raised when a plural translation is missing a placeholder.
    """


@final
class MissingPluralTag(LocaleError):
    """
    Raised when a countable localizable is missing a plural tag.
    """


@final
class InvalidPluralTag(LocaleError):
    """
    Raised when a countable localizable defines an invalid plural tag.
    """
