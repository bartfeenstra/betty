"""
Provide :py:class:`betty.copyright_notice.CopyrightNotice` plugins.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Self, final

import aiohttp
from aiohttp import ClientSession
from typing_extensions import override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.locale import DEFAULT_LOCALE, resolve_locale
from betty.locale.error import LocaleError
from betty.locale.localizable import resolve_localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import StaticTranslations
from betty.service.level import Manufacturable
from betty.service.requirement.app import require_app
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from betty.app import App
    from betty.locale.localizable import Localizable, ResolvableLocalizable
    from betty.project import Project


@final
@CopyrightNoticeDefinition("project-author", label=_("Project author"))
class ProjectAuthor(Manufacturable, CopyrightNotice):
    """
    .. plugin:: copyright-notice:project-author.
    """

    def __init__(self, author: ResolvableLocalizable | None):
        super().__init__()
        self._author = None if author is None else resolve_localizable(author)

    @override
    @classmethod
    @require_project
    async def new_for_services(cls, *, project: Project) -> Self:
        return cls(project.configuration.author)

    @property
    @override
    def summary(self) -> Localizable:
        if self._author:
            return _("© Copyright {author}, unless otherwise credited").format(
                author=self._author
            )
        return _("© Copyright the author, unless otherwise credited")

    @property
    @override
    def text(self) -> Localizable:
        return self.summary


@final
@CopyrightNoticeDefinition("public-domain", label=_("Public domain"))
class PublicDomain(CopyrightNotice):
    """
    .. plugin:: copyright-notice:public-domain.
    """

    @property
    @override
    def summary(self) -> Localizable:
        return _("Public domain")

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "Works in the public domain can be used or referenced without permission, because nobody holds any exclusive rights over these works (anymore)."
        )


@final
@CopyrightNoticeDefinition("streetmix", label=Plain("Streetmix LLC"))
class Streetmix(CopyrightNotice):
    """
    .. plugin:: copyright-notice:streetmix.
    """

    @override
    @property
    def summary(self) -> Localizable:
        return self.plugin().label

    @override
    @property
    def text(self) -> Localizable:
        return self.plugin().label

    @override
    @property
    def url(self) -> Localizable:
        return Plain("https://github.com/streetmix/streetmix")


def _copyright_url(language: str, page: str) -> str:
    return f"https://{language}.wikipedia.org/wiki/{page}"


@final
@CopyrightNoticeDefinition("wikipedia-contributors", label=_("Wikipedia contributors"))
class WikipediaContributors(Manufacturable, CopyrightNotice):
    """
    .. plugin:: copyright-notice:wikipedia-contributors.
    """

    def __init__(self, url: ResolvableLocalizable):
        super().__init__()
        self._url = resolve_localizable(url)

    @classmethod
    async def new(cls, *, http_client: ClientSession) -> Self:
        """
        Create a new instance.
        """
        urls = {
            DEFAULT_LOCALE: _copyright_url("en", "Wikipedia:Copyrights"),
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
    @classmethod
    @require_app
    async def new_for_services(cls, *, app: App) -> Self:
        return await cls.new(http_client=await app.http_client)

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
