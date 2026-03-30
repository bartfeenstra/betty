"""
The Wikipedia summary content plugin.
"""

from collections.abc import Iterable
from typing import Self, final, override

from babel import Locale

from betty.content import ContentDefinition
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.document import Document
from betty.entity.has_links import HasLinks
from betty.jinja import Environment
from betty.locale import negotiate_locale, resolve_locale
from betty.locale.localizable.gettext import _
from betty.locale.localize import LocalizerRepository
from betty.plugins.asset.wiki import Wiki as WikiAsset
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.link import Link
from betty.plugins.extension.wiki import Wiki as WikiExtension
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.wiki import NotAPageError, parse_page_url
from betty.wiki.client import Client, ClientError, Summary


@final
@ContentDefinition(
    "wikipedia-summary",
    label=_("Wikipedia summary"),
    requires={
        Project.assets.require(WikiAsset),
        Project.extensions.require(WikiExtension),
    },
)
class WikipediaSummary(Template, Manufacturable):
    """
    A Wikipedia summary.

    .. plugin:: content:wikipedia-summary
    """

    def __init__(
        self,
        *,
        client: Client,
        copyright_notice: CopyrightNotice,
        jinja: Environment,
        localizers: LocalizerRepository,
    ):
        super().__init__(jinja=jinja)
        self._client = client
        self._copyright_notice = copyright_notice
        self._localizers = localizers

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(
            client=await (await project.extensions[WikiExtension]).client,
            jinja=await project.jinja,
            localizers=await project.upstream.localizers,
            copyright_notice=await project.factory.new(
                (
                    await project.plugins[CopyrightNoticeDefinition][
                        "wikipedia-contributors"
                    ]
                ).cls
            ),
        )

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, HasLinks):
            summary = await self._get_summary(
                document.localizer.locale, document.resource.links
            )
            if summary:
                return "component/wiki/wikipedia-summary.html.j2", {
                    "wikipedia_summary": summary,
                    "wikipedia_summary_copyright_notice": self._copyright_notice,
                }
        return None

    async def _get_summary(
        self, locale: Locale, links: Iterable[Link]
    ) -> Summary | None:
        for link in links:
            try:
                page_language, page_name = parse_page_url(
                    link.url.localize(self._localizers.get(locale))
                )
            except NotAPageError:
                continue
            if (
                negotiate_locale(
                    locale, list(filter(None, [resolve_locale(page_language)]))
                )
                is None
            ):
                continue
            try:
                return await self._client.get_summary(page_language, page_name)
            except ClientError:
                continue
        return None
