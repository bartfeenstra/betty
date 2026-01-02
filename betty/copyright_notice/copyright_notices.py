"""
Provide :py:class:`betty.copyright_notice.CopyrightNotice` plugins.
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Self, final

import aiohttp
from aiohttp import ClientSession
from typing_extensions import override

from betty.app.factory import AppDependentSelfFactory
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.locale import DEFAULT_LOCALE, ensure_locale
from betty.locale.error import LocaleError
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.plain import Plain
from betty.locale.localizable.static import StaticTranslations
from betty.project.factory import ProjectDependentSelfFactory

if TYPE_CHECKING:
    from betty.app import App
    from betty.locale.localizable import Localizable, LocalizableLike
    from betty.project import Project


@final
@CopyrightNoticeDefinition("project-author", label=_("Project author"))
class ProjectAuthor(ProjectDependentSelfFactory, CopyrightNotice):
    """
    .. plugin:: copyright-notice:project-author.
    """

    def __init__(self, author: LocalizableLike | None):
        super().__init__()
        self._author = None if author is None else ensure_localizable(author)

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
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
class WikipediaContributors(AppDependentSelfFactory, CopyrightNotice):
    """
    .. plugin:: copyright-notice:wikipedia-contributors.
    """

    def __init__(self, url: LocalizableLike):
        super().__init__()
        self._url = ensure_localizable(url)

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
                    urls[ensure_locale(link["lang"])] = _copyright_url(
                        link["lang"], link["title"]
                    )
        return cls(StaticTranslations(urls))

    @override
    @classmethod
    async def new_for_app(cls, app: App, /) -> Self:
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
