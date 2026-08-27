"""
Generate URLs for URL paths.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Self, TypeGuard, final, override
from urllib.parse import urlencode

from betty.collections import _empty_frozen_mapping
from betty.factory import Arg1Manufacturable
from betty.locale import negotiate_locale, resolve_locale, to_language_tag
from betty.project import Project
from betty.url_generator import UrlGenerator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from babel import Locale

    from betty.locale import ResolvableLocale
    from betty.media_type import ResolvableMediaType


@final
class PathUrlGenerator(Arg1Manufacturable, UrlGenerator[str]):
    """
    Generate URLs for URL paths.
    """

    def __init__(
        self,
        *,
        base_url: str,
        root_path: str,
        locales_to_slugs: Mapping[Locale, str],
        clean_urls: bool,
    ):
        self._base_url = base_url
        self._root_path = root_path
        self._locales_to_slugs = locales_to_slugs
        assert len(locales_to_slugs)
        self.default_locale: Final[Locale] = next(iter(locales_to_slugs))
        self._clean_urls = clean_urls

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        """
        Create a new instance using the given project.
        """
        return cls(
            base_url=project.base_url,
            root_path=project.root_path,
            locales_to_slugs={
                project_locale.locale: project_locale.slug
                for project_locale in project.locales
            },
            clean_urls=project.clean_urls,
        )

    @override
    def supports(self, resource: Any, /) -> TypeGuard[str]:
        return isinstance(resource, str) and resource.startswith("/")

    @override
    def generate(
        self,
        resource: str,
        /,
        *,
        absolute: bool = False,
        fragment: str | None = None,
        locale: ResolvableLocale | None = None,
        media_type: ResolvableMediaType | None = None,
        query: Mapping[str, Sequence[str]] = _empty_frozen_mapping,
    ) -> str:
        url = self._base_url.rstrip("/") if absolute else ""
        url += self._root_path.rstrip("/")
        assert resource.startswith("/"), (
            f'Paths must be root-relative (start with a forward slash), but "{resource}" was given'
        )
        path = resource.strip("/")
        if locale and len(self._locales_to_slugs) > 1:
            locale = resolve_locale(locale)
            try:
                negotiated_locale = negotiate_locale(
                    locale, list(self._locales_to_slugs)
                )
                if negotiated_locale is None:
                    raise KeyError  # noqa: TRY301
                locale_slug = self._locales_to_slugs[negotiated_locale]
            except KeyError:
                raise ValueError(
                    f'Cannot generate URLs in "{locale}", because it cannot be resolved to any of the available locales: {", ".join(map(to_language_tag, self._locales_to_slugs))}'
                ) from None
            url += f"/{locale_slug}"
        if path:
            url += f"/{path}"
        if self._clean_urls and url.endswith("/index.html"):
            url = url[:-11]
        # Ensure URLs are root-relative.
        if not absolute:
            url = f"/{url.lstrip('/')}"
        if query:
            url += "?" + urlencode(query)
        if fragment is not None:
            url += "#" + fragment
        return url
