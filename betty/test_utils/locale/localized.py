"""
Test utilities for :py:mod:`betty.locale.localized`.
"""

from betty.locale.localized import Localized


class DummyLocalized(Localized):
    """
    A dummy :py:class:`betty.locale.localized.Localized` implementation.
    """

    def __init__(self, locale: str):
        self._locale = locale
