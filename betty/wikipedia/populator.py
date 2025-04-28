"""
Populate ancestries with information from Wikipedia.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from contextlib import suppress
from typing import TYPE_CHECKING

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.link import HasLinks, Link
from betty.ancestry.place import Place
from betty.concurrent import AsynchronizedLock, Lock
from betty.fetch import FetchError
from betty.functools import filter_suppress
from betty.locale import (
    UNDETERMINED_LOCALE,
    Localey,
    get_data,
    negotiate_locale,
    to_locale,
)
from betty.locale.error import LocaleError
from betty.media_type.media_types import HTML
from betty.typing import internal, threadsafe
from betty.wikipedia import NotAPageError, parse_page_url

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence

    from betty.ancestry import Ancestry
    from betty.locale.localizer import LocalizerRepository
    from betty.wikipedia.client import Client, Image, Summary
    from betty.wikipedia.copyright_notice import WikipediaContributors


@internal
@threadsafe
class Populator:
    """
    Populate an ancestry with information from Wikipedia.
    """

    def __init__(
        self,
        ancestry: Ancestry,
        locales: Sequence[str],
        localizers: LocalizerRepository,
        client: Client,
        copyright_notice: WikipediaContributors,
    ):
        self._ancestry = ancestry
        self._locales = locales
        self._localizers = localizers
        self._client = client
        self._image_files: MutableMapping[Image, File] = {}
        self._image_files_locks: Mapping[Image, Lock] = defaultdict(
            AsynchronizedLock.threading
        )
        self._copyright_notice = copyright_notice

    async def populate(self) -> None:
        """
        Populate the ancestry.
        """
        await gather(
            *(
                self._populate_entity(entity, self._locales)
                for entity in self._ancestry
                if isinstance(entity, HasLinks)
            )
        )

    async def _populate_entity(self, entity: HasLinks, locales: Sequence[str]) -> None:
        populations = [self._populate_has_links(entity, locales)]
        if isinstance(entity, HasFileReferences):
            populations.append(self._populate_has_file_references(entity))
        if isinstance(entity, Place):
            populations.append(self._populate_place(entity))
        await gather(*populations)

    async def _populate_has_links(
        self, has_links: HasLinks, locales: Sequence[str]
    ) -> None:
        summary_links: MutableSequence[tuple[str, str]] = []
        for link in has_links.links:
            try:
                page_language, page_name = parse_page_url(link.url)
            except NotAPageError:
                continue
            else:
                try:
                    get_data(page_language)
                except LocaleError:
                    continue
                else:
                    summary_links.append((page_language, page_name))

            summary = None
            if not link.label:
                with suppress(FetchError):
                    summary = await self._client.get_summary(page_language, page_name)
            await self._populate_link(link, page_language, summary)
        await self._populate_has_links_with_translation(
            has_links, locales, summary_links
        )

    async def _populate_has_links_with_translation(
        self,
        has_links: HasLinks,
        locales: Sequence[str],
        summary_links: MutableSequence[tuple[str, str]],
    ) -> None:
        for page_language, page_name in summary_links:
            page_translations = await self._client.get_translations(
                page_language, page_name
            )
            if len(page_translations) == 0:
                continue
            page_translation_locale_datas: Sequence[Localey] = list(
                filter_suppress(get_data, LocaleError, page_translations.keys())
            )
            for locale in locales:
                if locale == page_language:
                    continue
                added_page_locale_data = negotiate_locale(
                    locale, page_translation_locale_datas
                )
                if added_page_locale_data is None:
                    continue
                added_page_language = to_locale(added_page_locale_data)
                added_page_name = page_translations[added_page_language]
                if (added_page_language, added_page_name) in summary_links:
                    continue
                added_summary = await self._client.get_summary(
                    added_page_language, added_page_name
                )
                if not added_summary:
                    continue
                added_link = Link(added_summary.url)
                await self._populate_link(
                    added_link, added_page_language, added_summary
                )
                has_links.links.append(added_link)
                summary_links.append((added_page_language, added_page_name))
            return

    async def _populate_link(
        self, link: Link, summary_language: str, summary: Summary | None = None
    ) -> None:
        if link.url.startswith("http:"):
            link.url = "https:" + link.url[5:]
        if link.media_type is None:
            link.media_type = HTML
        if link.relationship is None:
            link.relationship = "external"
        if link.locale is UNDETERMINED_LOCALE:
            link.locale = summary_language
        if not link.description:
            # There are valid reasons for links in locales that aren't supported.
            with suppress(ValueError):
                link.description = (
                    await self._localizers.get_negotiated(link.locale)
                )._("Read more on Wikipedia.")
        if summary is not None and not link.label:
            link.label[summary_language] = summary.title

    async def _populate_place(self, place: Place) -> None:
        await self._populate_place_coordinates(place)

    async def _populate_place_coordinates(self, place: Place) -> None:
        await gather(
            *(
                self._populate_place_coordinates_link(place, link)
                for link in place.links
            )
        )

    async def _populate_place_coordinates_link(self, place: Place, link: Link) -> None:
        try:
            page_language, page_name = parse_page_url(link.url)
        except NotAPageError:
            return
        else:
            coordinates = await self._client.get_place_coordinates(
                page_language, page_name
            )
            if coordinates:
                place.coordinates = coordinates

    async def _populate_has_file_references(
        self, has_file_references: HasFileReferences & HasLinks
    ) -> None:
        await gather(
            *(
                self._populate_has_file_references_link(has_file_references, link)
                for link in has_file_references.links
            )
        )

    async def _populate_has_file_references_link(
        self, has_file_references: HasFileReferences & HasLinks, link: Link
    ) -> None:
        try:
            page_language, page_name = parse_page_url(link.url)
        except NotAPageError:
            return
        else:
            image = await self._client.get_image(page_language, page_name)
            if not image:
                return
            await self._image_file_reference(has_file_references, image)

    async def _image_file_reference(
        self, has_file_references: HasFileReferences, image: Image
    ) -> FileReference:
        async with self._image_files_locks[image]:
            try:
                file = self._image_files[image]
            except KeyError:
                links = []
                for locale in self._locales:
                    localizer = await self._localizers.get(locale)
                    links.append(
                        Link(
                            f"{image.wikimedia_commons_url}?uselang={locale}",
                            label=localizer._(
                                "Description, licensing, and image history"
                            ),
                            description=localizer._(
                                "Find out more about this image on Wikimedia Commons."
                            ),
                            locale=locale,
                            media_type=HTML,
                        )
                    )
                file = File(
                    id=f"wikipedia-{image.title}",
                    name=image.name,
                    path=image.path,
                    media_type=image.media_type,
                    links=links,
                    copyright_notice=self._copyright_notice,
                )
                self._image_files[image] = file
                self._ancestry.add(file)
            file_reference = FileReference(has_file_references, file)
            self._ancestry.add(file_reference)
            return file_reference
