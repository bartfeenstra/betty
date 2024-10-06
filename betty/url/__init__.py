"""
Provide a URL generation API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING, Self

from betty.locale import negotiate_locale, Localey, to_locale

if TYPE_CHECKING:
    from betty.media_type import MediaType
    from collections.abc import Mapping


class UnsupportedResource(RuntimeError):
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


class _UrlGenerator(ABC):
    """
    Generate URLs for localizable resources.
    """

    @abstractmethod
    def supports(self, resource: Any) -> bool:
        """
        Whether the given resource is supported by this URL generator.
        """
        pass


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
        Generate a localized URL for a localizable resource.

        :raise UnsupportedResource:
        """
        pass


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
        """
        pass


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
    assert path.startswith(
        "/"
    ), f'Paths must be root-relative (start with a forward slash), but "{path}" was given'
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
