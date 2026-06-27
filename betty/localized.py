"""
The localized API, to describe data that is localized.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final, override

if TYPE_CHECKING:
    from babel import Locale


class Localized(ABC):
    """
    A resource that has a locale, e.g. contains information in a specific locale.
    """

    @property
    @abstractmethod
    def locale(self) -> Locale | None:
        """
        The locale the data in this instance is in.
        """


@final
class LocalizedStr(Localized, str):
    """
    A string that has a locale.
    """

    __slots__ = ("_locale",)

    _locale: Locale | None

    @override
    def __new__(cls, string: str, /, *, locale: Locale | None = None):
        new = super().__new__(cls, string)
        new._locale = locale
        return new

    def __init__(self, string: str, *, locale: Locale | None = None):
        pass

    @override
    @property
    def locale(self) -> Locale | None:
        return self._locale
