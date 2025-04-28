"""
Provide a URL generation API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Self
from urllib.parse import urlparse

from typing_extensions import deprecated, override

from betty.locale import Localey, negotiate_locale, to_locale

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.media_type import MediaType


class GenerationError(RuntimeError):
    """
    A URL generation error.
    """


class UnsupportedResource(GenerationError):
    """
    Raised when a URL generator cannot generate a URL for a resource.

    These are preventable by checking :py:meth:`betty.url.LocalizedUrlGenerator.supports` or
    :py:meth:`betty.url.StaticUrlGenerator.supports` first.
    """

    @classmethod
    def new(cls, resource: Any) -> Self:
        """
        Create a new instance.
        """
        return cls(f"Unsupported resource: {resource}")


class InvalidMediaType(GenerationError):
    """
    Raised when a URL generator cannot generate a URL for a resource with the given media type.
    """

    @classmethod
    def new(cls, resource: Any, media_type: MediaType | None) -> Self:
        """
        Create a new instance.
        """
        if media_type:
            return cls(f"Unsupported media type '{media_type}' for resource {resource}")
        return cls(f"Missing media type for resource {resource}")


class _UrlGenerator(ABC):
    """
    Generate URLs for localizable resources.
    """

    @abstractmethod
    def supports(self, resource: Any) -> bool:
        """
        Whether the given resource is supported by this URL generator.
        """


class UrlGenerator(_UrlGenerator):
    """
    Generate URLs for resources.
    """

    @abstractmethod
    def generate(
        self,
        resource: Any,
        *,
        media_type: MediaType | None = None,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        """
        Generate a URL for a resource.

        :raise UnsupportedResource:
        :raise InvalidMediaType:
        """


@deprecated(
    f"This class has been deprecated since Betty 0.4.8, and will be removed in Betty 0.5. Instead use {UrlGenerator}."
)
class LocalizedUrlGenerator(_UrlGenerator):
    """
    Generate URLs for localizable resources.
    """

    @abstractmethod
    def generate(
        self,
        resource: Any,
        media_type: MediaType,
        *,
        absolute: bool = False,
        locale: Localey | None = None,
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
        media_type: MediaType | None = None,
        absolute: bool = False,
        locale: Localey | None = None,
    ) -> str:
        assert isinstance(resource, str)
        return resource


@deprecated(
    f"This class has been deprecated since Betty 0.4.8, and will be removed in Betty 0.5. Instead use {UrlGenerator}."
)
class StaticUrlGenerator(_UrlGenerator):
    """
    Generate URLs for static (non-localizable) resources.
    """

    @abstractmethod
    def generate(
        self,
        resource: Any,
        *,
        absolute: bool = False,
    ) -> str:
        """
        Generate a static URL for a static resource.

        :raise UnsupportedResource:
        :raise InvalidMediaType:
        """


def generate_from_path(
    path: str,
    *,
    base_url: str,
    root_path: str,
    locales: Mapping[str, str],
    clean_urls: bool,
    absolute: bool = False,
    locale: Localey | None = None,
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
    if locale and len(locales) > 1:
        locale = to_locale(locale)
        try:
            negotiated_locale_data = negotiate_locale(locale, list(locales))
            if negotiated_locale_data is None:
                raise KeyError
            locale_alias = locales[to_locale(negotiated_locale_data)]
        except KeyError:
            raise ValueError(
                f'Cannot generate URLs in "{locale}", because it cannot be resolved to any of the available locales: {", ".join(locales)}'
            ) from None
        url += f"/{locale_alias}"
    if path:
        url += f"/{path}"
    if clean_urls and url.endswith("/index.html"):
        url = url[:-11]
    # Ensure URLs are root-relative.
    if not absolute:
        url = f"/{url.lstrip('/')}"
    return url
