"""
Data indicators.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, final, override

from betty.pathlib import resolve_path

if TYPE_CHECKING:
    from betty.pathlib import StrPath


class Indicator(metaclass=ABCMeta):
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

    def __init__(self, path: StrPath, /):
        self._path = resolve_path(path).resolve().absolute()

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
