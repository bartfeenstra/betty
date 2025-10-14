"""
Jobs.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from typing import TYPE_CHECKING, final

from aiohttp import ClientError
from html5lib import parse
from typing_extensions import override

from betty.job import Job
from betty.locale.localizable import StaticTranslations
from betty.media_type import InvalidMediaType, MediaType
from betty.project import Project, ProjectContext

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping
    from xml.etree.ElementTree import Element

    from betty.ancestry.link import Link
    from betty.job.scheduler import Scheduler


@final
class PopulateLink(Job[ProjectContext]):
    """
    Populate a link with information from its URL.
    """

    def __init__(self, link: Link):
        super().__init__(self.id_for(link), priority=True)
        self._link = link

    @classmethod
    def id_for(cls, link: Link) -> str:
        """
        Get the job ID.
        """
        return f"populate-link:{link.id}"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        if self._link.has_label and self._link.description:
            return

        project = scheduler.context.project

        localizers = await project.localizers
        urls = StaticTranslations.from_localizable(
            self._link.url,
            [localizers.get(locale) for locale in project.configuration.locales],
        )
        urls_to_locales = defaultdict(set)
        for locale, url in urls.translations.items():
            urls_to_locales[url].add(locale)
        labels: MutableMapping[str, str] = {}
        descriptions: MutableMapping[str, str] = {}
        await gather(
            *(
                self._populate_link_from_url(
                    project,
                    url,
                    project.configuration.locales,
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
        project: Project,
        url: str,
        locales: Iterable[str],
        labels: MutableMapping[str, str],
        descriptions: MutableMapping[str, str],
    ) -> None:
        http_client = await project.app.http_client
        try:
            response = await http_client.get(url)
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

        document = parse(await response.text())
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

    def _extract_html_title(self, document: Element) -> str | None:
        head = document.find(
            "ns:head",
            namespaces={
                "ns": "http://www.w3.org/1999/xhtml",
            },
        )
        if head is None:
            return None
        title = head.find(
            "ns:title",
            namespaces={
                "ns": "http://www.w3.org/1999/xhtml",
            },
        )
        if title is None:
            return None
        return title.text

    def _extract_html_meta_description(self, document: Element) -> str | None:
        head = document.find(
            "ns:head",
            namespaces={
                "ns": "http://www.w3.org/1999/xhtml",
            },
        )
        if head is None:
            return None
        metas = head.findall(
            "ns:meta",
            namespaces={
                "ns": "http://www.w3.org/1999/xhtml",
            },
        )
        for attr_name, attr_value in (
            ("name", "description"),
            ("property", "og:description"),
        ):
            for meta in metas:
                if meta.get(attr_name, None) == attr_value:
                    return meta.get("content", None)
        return None
