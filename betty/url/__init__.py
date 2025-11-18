"""
Provide a URL generation API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode, urlparse

from typing_extensions import override

from betty.locale import LocaleLike, negotiate_locale, to_locale

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from betty.media_type import MediaType


class GenerationError(RuntimeError):
    """
    A URL generation error.
    """


class UnsupportedResource(GenerationError):
    """
    Raised when a URL generator cannot generate a URL for a resource.

    These are preventable by checking :py:meth:`betty.url.UrlGenerator.supports` first.
    """

    def __init__(self, resource: Any):
        super().__init__(f"Unsupported resource: {resource}")


class InvalidMediaType(GenerationError):
    """
    Raised when a URL generator cannot generate a URL for a resource with the given media type.
    """

    def __init__(self, resource: Any, media_type: MediaType | None):
        super().__init__(
            f"Unsupported media type '{media_type}' for resource {resource}"
            if media_type
            else f"Missing media type for resource {resource}"
        )


class UrlGenerator(ABC):
    """
    Generate URLs for resources.
    """

    @abstractmethod
    def supports(self, resource: Any) -> bool:
        """
        Whether the given resource is supported by this URL generator.
        """

    @abstractmethod
    def generate(
        self,
        resource: Any,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: LocaleLike | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        """
        Generate a URL for a resource.

        :raise UnsupportedResource:
        :raise InvalidMediaType:
        """


class PassthroughUrlGenerator(UrlGenerator):
    """
    Returns resources verbatim if they are absolute URLs already.
    """

    @override
    def supports(self, resource: Any) -> bool:
        if not isinstance(resource, str):
            return False
        try:
            return bool(urlparse(resource).scheme)
        except ValueError:
            return False

    @override
    def generate(
        self,
        resource: Any,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: LocaleLike | None = None,
        media_type: MediaType | None = None,
        query: Mapping[str, Sequence[str]] | None = None,
    ) -> str:
        assert isinstance(resource, str)
        return resource


def generate_from_path(
    path: str,
    *,
    base_url: str,
    clean_urls: bool,
    root_path: str,
    absolute: bool = False,
    fragment: str | None = None,
    locale: LocaleLike | None = None,
    locale_aliases: Mapping[str, str],
    query: Mapping[str, Sequence[str]] | None = None,
) -> str:
    """
    Generate a full URL from a public path.
    """
    url = base_url.rstrip("/") if absolute else ""
    url += root_path.rstrip("/")
    assert path.startswith("/"), (
        f'Paths must be root-relative (start with a forward slash), but "{path}" was given'
    )
    path = path.strip("/")
    if locale and len(locale_aliases) > 1:
        locale = to_locale(locale)
        try:
            negotiated_locale_data = negotiate_locale(locale, list(locale_aliases))
            if negotiated_locale_data is None:
                raise KeyError
            locale_alias = locale_aliases[to_locale(negotiated_locale_data)]
        except KeyError:
            raise ValueError(
                f'Cannot generate URLs in "{locale}", because it cannot be resolved to any of the available locales: {", ".join(locale_aliases)}'
            ) from None
        url += f"/{locale_alias}"
    if path:
        url += f"/{path}"
    if clean_urls and url.endswith("/index.html"):
        url = url[:-11]
    # Ensure URLs are root-relative.
    if not absolute:
        url = f"/{url.lstrip('/')}"
    if query is not None:
        url += "?" + urlencode(query)
    if fragment is not None:
        url += "#" + fragment
    return url
