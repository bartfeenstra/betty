"""
Fetch content from the internet.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import loads
from pathlib import Path
from typing import Any, TypeVar

from multidict import CIMultiDict

from betty.error import UserFacingError

_CacheItemValueT = TypeVar("_CacheItemValueT")


class FetchError(UserFacingError, RuntimeError):
    """
    An error that occurred when fetching a URL.
    """

    pass  # pragma: no cover


@dataclass
class FetchResponse:
    """
    An HTTP response.
    """

    headers: CIMultiDict[str]
    body: bytes
    encoding: str

    @property
    def text(self) -> str:
        """
        The body as plain text.

        This may raise an error if the response body cannot be represented as plain text.
        """
        return self.body.decode(self.encoding)

    @property
    def json(self) -> Any:
        """
        The body as JSON.

        This may raise an error if the response body cannot be represented as JSON or plain text.
        """
        return loads(self.text)


class Fetcher(ABC):
    """
    Fetch content from the internet.
    """

    @abstractmethod
    async def fetch(self, url: str) -> FetchResponse:
        """
        Fetch an HTTP resource.
        """
        pass

    @abstractmethod
    async def fetch_file(self, url: str) -> Path:
        """
        Fetch a file.

        :return: The path to the file on disk.
        """
        pass
