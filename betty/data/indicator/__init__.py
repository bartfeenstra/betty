"""
Data indicators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final, override

if TYPE_CHECKING:
    import pathlib


class Indicator(ABC):
    """
    Describe a location of a piece of data.
    """

    @abstractmethod
    def format(self) -> str:
        """
        Format the indicator to a string.
        """


@final
class AnyIndex(Indicator):
    """
    A sequence item indicator.
    """

    @override
    def format(self) -> str:
        return "[]"


@final
class AnyKey(Indicator):
    """
    A mapping item indicator.
    """

    @override
    def format(self) -> str:
        return "{}"


@final
class Path(Indicator):
    """
    A file on disk.
    """

    def __init__(self, path: pathlib.Path, /):
        self._path = path.resolve().absolute()

    @override
    def format(self) -> str:
        return str(self._path)


@final
class Url(Indicator):
    """
    A URL.
    """

    def __init__(self, url: str, /):
        self._url = url

    @override
    def format(self) -> str:
        return self._url
