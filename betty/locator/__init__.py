"""
The locator API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, final, override

from betty.pathlib import resolve_path

if TYPE_CHECKING:
    from betty.pathlib import StrPath


class Locator(metaclass=ABCMeta):
    """
    Describe a location of a piece of data.
    """

    __slots__ = ()

    @abstractmethod
    def format(self) -> str:
        """
        Format the locator to a string.
        """


@final
class AnyIndex(Locator):
    """
    A sequence item locator.
    """

    @override
    def format(self) -> str:
        return "[]"


@final
class AnyKey(Locator):
    """
    A mapping item locator.
    """

    @override
    def format(self) -> str:
        return "{}"


@final
class Path(Locator):
    """
    A file on disk.
    """

    def __init__(self, path: StrPath, /):
        self._path = resolve_path(path).resolve().absolute()

    @override
    def format(self) -> str:
        return str(self._path)


@final
class Url(Locator):
    """
    A URL.
    """

    def __init__(self, url: str, /):
        self._url = url

    @override
    def format(self) -> str:
        return self._url
