"""
Jobs to populate links.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, final, override

from aiohttp import ClientError, ClientSession
from lxml.html import HtmlElement, document_fromstring

from betty.job import Job
from betty.localizables.static import StaticTranslations
from betty.media_type import InvalidMediaType, MediaType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.entities.link import Link
    from betty.job.scheduler import Scheduler
    from betty.localizer import Localizer


@final
@dataclass(frozen=True, slots=True)
class _Population:
    label: str | None
    description: str | None


@final
class PopulateLink(Job):
    """
    Populate a link with information from its URL.
    """

    def __init__(
        self,
        link: Link,
        /,
        *,
        http_client: ClientSession,
        localizers: Iterable[Localizer],
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
        if self._link.has_label or self._link.description:
            return

        locales_to_urls = StaticTranslations.resolve(
            self._link.url, self._localizers
        ).translations
        urls = set(locales_to_urls.values())
        urls_to_populations = defaultdict(
            lambda: None,
            zip(urls, await gather(*map(self._get_population, urls)), strict=False),
        )
        if not self._link.has_label:
            labels = {
                locale: label
                for locale, url in locales_to_urls.items()
                if (population := urls_to_populations[url])
                and (label := population.label)
            }
            if labels:
                self._link.label = StaticTranslations(labels)
        if not self._link.description:
            descriptions = {
                locale: description
                for locale, url in locales_to_urls.items()
                if (population := urls_to_populations[url])
                and (description := population.description)
            }
            if descriptions:
                self._link.description = StaticTranslations(descriptions)

    async def _get_population(self, url: str) -> _Population | None:
        try:
            response = await self._http_client.get(url)
        except ClientError:
            return None
        try:
            content_type = MediaType(response.headers["Content-Type"])
        except InvalidMediaType:
            return None

        if (content_type.type, content_type.subtype, content_type.suffix) not in (
            ("text", "html", None),
            ("application", "xhtml", "+xml"),
        ):
            return None

        document = document_fromstring(await response.text())
        return _Population(
            self._extract_html_title(document),
            self._extract_html_meta_description(document),
        )

    def _extract_html_title(self, document: HtmlElement) -> str | None:
        if self._link.has_label:
            return None
        head = document.find("head")
        if head is None:
            return None
        title = head.find("title")
        if title is None:
            return None
        return title.text

    def _extract_html_meta_description(self, document: HtmlElement) -> str | None:
        if self._link.description:
            return None
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
