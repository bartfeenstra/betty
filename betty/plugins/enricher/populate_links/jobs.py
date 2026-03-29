"""
Jobs.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from typing import TYPE_CHECKING, final, override

from aiohttp import ClientError, ClientSession
from lxml.html import HtmlElement, document_fromstring

from betty.job import Job
from betty.locale.localizable.static import StaticTranslations
from betty.media_type import InvalidMediaType, MediaType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from babel import Locale

    from betty.job.scheduler import Scheduler
    from betty.locale.localizable import StaticTranslationsMapping
    from betty.locale.localize import Localizer
    from betty.plugins.entity.link import Link


@final
class PopulateLink(Job):
    """
    Populate a link with information from its URL.
    """

    def __init__(
        self, link: Link, *, http_client: ClientSession, localizers: Iterable[Localizer]
    ):
        super().__init__(self.id_for(link), priority=True)
        self._link = link
        self._http_client = http_client
        self._localizers = localizers

    @classmethod
    def id_for(cls, link: Link) -> str:
        """
        Get the job ID.
        """
        return f"populate-link:{link.id}"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        if self._link.has_label and self._link.description:
            return

        urls = StaticTranslations.resolve(self._link.url, self._localizers)
        urls_to_locales = defaultdict(set)
        for locale, url in urls.translations.items():
            urls_to_locales[url].add(locale)
        labels: StaticTranslationsMapping = {}
        descriptions: StaticTranslationsMapping = {}
        await gather(
            *(
                self._populate_link_from_url(
                    url,
                    [localizer.locale for localizer in self._localizers],
                    labels,
                    descriptions,
                )
                for url in urls_to_locales
            )
        )
        if not self._link.has_label and labels:
            self._link.label = StaticTranslations(labels)
        if not self._link.description and descriptions:
            self._link.description = StaticTranslations(descriptions)

    async def _populate_link_from_url(
        self,
        url: str,
        locales: Iterable[Locale],
        labels: StaticTranslationsMapping,
        descriptions: StaticTranslationsMapping,
    ) -> None:
        try:
            response = await self._http_client.get(url)
        except ClientError:
            return
        try:
            content_type = MediaType(response.headers["Content-Type"])
        except InvalidMediaType:
            return

        if (content_type.type, content_type.subtype, content_type.suffix) not in (
            ("text", "html", None),
            ("application", "xhtml", "+xml"),
        ):
            return

        document = document_fromstring(await response.text())
        if not self._link.has_label:
            title = self._extract_html_title(document)
            if title is not None:
                for locale in locales:
                    labels[locale] = title
        if not self._link.description:
            description = self._extract_html_meta_description(document)
            if description is not None:
                for locale in locales:
                    descriptions[locale] = description

    def _extract_html_title(self, document: HtmlElement) -> str | None:
        head = document.find("head")
        if head is None:
            return None
        title = head.find("title")
        if title is None:
            return None
        return title.text

    def _extract_html_meta_description(self, document: HtmlElement) -> str | None:
        head = document.find("head")
        if head is None:
            return None
        metas = head.findall("meta")
        for attr_name, attr_value in (
            ("name", "description"),
            ("property", "og:description"),
        ):
            for meta in metas:
                if meta.get(attr_name, None) == attr_value:
                    return meta.get("content", None)
        return None
