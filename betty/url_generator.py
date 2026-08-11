"""
Provide a URL generation API.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, TypeGuard

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.locale import ResolvableLocale
    from betty.media_type import ResolvableMediaType


class GenerationError(RuntimeError):
    """
    A URL generation error.
    """


class UnsupportedResource(GenerationError):
    """
    Raised when a URL generator cannot generate a URL for a resource.

    These are preventable by checking :py:meth:`betty.url_generator.UrlGenerator.supports` first.
    """

    def __init__(self, resource: Any, /):
        super().__init__(f"Unsupported resource: {resource}")


class UrlGenerator[ResourceT](metaclass=ABCMeta):
    """
    Generate URLs for resources.
    """

    @abstractmethod
    def supports(self, resource: Any, /) -> TypeGuard[ResourceT]:
        """
        Whether the given resource is supported by this URL generator.
        """

    @abstractmethod
    def generate(
        self,
        resource: ResourceT,
        /,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: ResolvableMediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        """
        Generate a URL for a resource.

        :raise UnsupportedResource:
        :raise UnsupportedMediaType:
        """
