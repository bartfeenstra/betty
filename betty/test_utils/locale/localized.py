"""
Test utilities for :py:mod:`betty.locale.localized`.
"""

from betty.locale import LocaleLike, ensure_locale
from betty.locale.localized import Localized


class DummyLocalized(Localized):
    """
    A dummy :py:class:`betty.locale.localized.Localized` implementation.
    """

    def __init__(self, locale: LocaleLike | None = None):
        self._locale = None if locale is None else ensure_locale(locale)
