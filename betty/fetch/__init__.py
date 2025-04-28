"""
Fetch content from the internet.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import loads
from pathlib import Path
from typing import Any, final

from multidict import CIMultiDict

from betty.error import UserFacingError


class FetchError(UserFacingError, RuntimeError):
    """
    An error that occurred when fetching a URL.
    """


@final
@dataclass(frozen=True)
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

        :raises FetchError: if an error occurred while fetching the content.
        """

    @abstractmethod
    async def fetch_file(self, url: str) -> Path:
        """
        Fetch a file.

        :raises FetchError: if an error occurred while fetching the content.

        :return: The path to the file on disk.
        """
