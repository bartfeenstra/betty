"""
The Wikipedia contributors copyright notice.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Self, final, override

import aiohttp

from betty.app import App
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.factory import Arg1Manufacturable
from betty.locale import default_locale, resolve_locale
from betty.locale.error import LocaleError
from betty.localizable import (
    Localizable,
    ResolvableLocalizable,
    StaticTranslationsMapping,
    resolve_localizable,
)
from betty.localizables.gettext import _
from betty.localizables.static import StaticTranslations
from betty.service_level import ResolvableServiceLevel


def _copyright_url(language: str, page: str) -> str:
    return f"https://{language}.wikipedia.org/wiki/{page}"


@final
@CopyrightNoticeDefinition("wikipedia-contributors", label=_("Wikipedia contributors"))
class WikipediaContributors(
    Arg1Manufacturable[ResolvableServiceLevel[App]], CopyrightNotice
):
    """
    .. plugin:: copyright-notice:wikipedia-contributors.
    """

    def __init__(self, url: ResolvableLocalizable):
        super().__init__()
        self._url = resolve_localizable(url)

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        http_client = await app.http_client
        urls: StaticTranslationsMapping = {
            default_locale: _copyright_url("en", "Wikipedia:Copyrights"),
        }
        try:
            response = await http_client.get(
                "https://en.wikipedia.org/w/api.php?action=query&titles=Wikipedia:Copyrights&prop=langlinks&lllimit=500&format=json&formatversion=2"
            )
            response_json = await response.json()
        except aiohttp.ClientError:
            pass
        else:
            for link in response_json["query"]["pages"][0][
                "langlinks"
            ]:  # typing: ignore[index]
                # Wikipedia uses some languages that are not valid ISO codes, such as "simple".
                with suppress(LocaleError):
                    urls[resolve_locale(link["lang"])] = _copyright_url(
                        link["lang"], link["title"]
                    )
        return cls(StaticTranslations(urls))

    @override
    @property
    def summary(self) -> Localizable:
        return _("Copyright Wikipedia contributors")

    @override
    @property
    def text(self) -> Localizable:
        return _(
            "Copyright of these works lies with the original authors who contributed them to Wikipedia."
        )

    @override
    @property
    def url(self) -> Localizable:
        return self._url
