"""
Populate ancestries with information from Wikipedia and Wikimedia.
"""

from __future__ import annotations

from asyncio import gather
from collections import defaultdict
from typing import TYPE_CHECKING

from aiohttp import ClientError

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.ancestry.has_file_references import HasFileReferences
from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.ancestry.place import Place
from betty.concurrent import AsynchronizedLock, Lock
from betty.functools import filter_suppress
from betty.locale import get_data, negotiate_locale
from betty.locale.error import LocaleError
from betty.locale.localizable import StaticTranslations, _
from betty.media_type.media_types import HTML
from betty.typing import threadsafe
from betty.wiki import NotAPageError, parse_page_link

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping, Sequence

    from betty.ancestry import Ancestry
    from betty.copyright_notice import CopyrightNotice
    from betty.locale.localizer import LocalizerRepository
    from betty.model import Entity
    from betty.wiki.client import Client, Image


@threadsafe
class Populator:
    """
    Populate an ancestry with information from Wikipedia and Wikimedia.
    """

    def __init__(
        self,
        ancestry: Ancestry,
        locales: Sequence[str],
        localizers: LocalizerRepository,
        client: Client,
        copyright_notice: CopyrightNotice,
    ):
        self._ancestry = ancestry
        self._locales = locales
        self._localizers = localizers
        self._client = client
        self._image_files: MutableMapping[Image, File] = {}
        self._image_files_locks: Mapping[Image, Lock] = defaultdict(
            AsynchronizedLock.new_threadsafe
        )
        self._copyright_notice = copyright_notice

    async def populate(self, entity: Entity) -> None:
        """
        Populate an entity.
        """
        populations = []
        if isinstance(entity, HasFileReferences) and isinstance(entity, HasLinks):
            populations.append(self._populate_has_file_references_and_links(entity))
        if isinstance(entity, Place):
            populations.append(self._populate_place(entity))
        if isinstance(entity, Link):
            populations.append(self._populate_link(entity))
        await gather(*populations)

    async def _populate_link(self, link: Link) -> None:
        try:
            page_language, page_name = parse_page_link(
                link, [self._localizers.get(locale) for locale in self._locales]
            )
        except NotAPageError:
            return
        if link.media_type is None:
            link.media_type = HTML
        if link.relationship is None:
            link.relationship = "external"
        if link.description is None:
            link.description = _("Read more on Wikipedia.")
        try:
            page_translations = dict(
                await self._client.get_translations(page_language, page_name)
            )
        except ClientError:
            return
        if page_translations:
            # For convenience, we add the original page language and name to the available translations.
            page_translations[page_language] = page_name

            # Most Wikipedia languages are based on ISO 639-1 and ISO 639-3
            # (https://en.wikipedia.org/wiki/List_of_Wikipedias). However, some languages such as "simple" are not.
            translation_page_locale_datas = list(
                filter_suppress(get_data, LocaleError, page_translations)
            )

            locales_to_page_languages = {}
            for locale in self._locales:
                negotiated_page_language = negotiate_locale(
                    locale, translation_page_locale_datas
                )
                locales_to_page_languages[locale] = (
                    page_language
                    if negotiated_page_language is None
                    else str(negotiated_page_language)
                )

            link.url = StaticTranslations(
                {
                    locale: f"https://{page_language}.wikipedia.org/wiki/{page_translations[page_language]}"
                    for locale, page_language in locales_to_page_languages.items()
                }
            )
            if not link.has_label:
                link.label = StaticTranslations(
                    {
                        locale: await self._fetch_link_label_from_page(
                            page_language, page_translations[page_language]
                        )
                        or page_name
                        for locale, page_language in locales_to_page_languages.items()
                    }
                )

    async def _fetch_link_label_from_page(
        self, page_language: str, page_name: str
    ) -> str | None:
        summary = await self._client.get_summary(page_language, page_name)
        return summary.title

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
            page_language, page_name = parse_page_link(
                link, [self._localizers.get(locale) for locale in self._locales]
            )
        except NotAPageError:
            return
        else:
            coordinates = await self._client.get_place_coordinates(
                page_language, page_name
            )
            if coordinates:
                place.coordinates = coordinates

    async def _populate_has_file_references_and_links(
        self, has_file_references: HasFileReferences & HasLinks
    ) -> None:
        await gather(
            *(
                self._populate_has_file_references_and_links_link(
                    has_file_references, link
                )
                for link in has_file_references.links
            )
        )

    async def _populate_has_file_references_and_links_link(
        self, has_file_references: HasFileReferences, link: Link
    ) -> None:
        try:
            page_language, page_name = parse_page_link(
                link, [self._localizers.get(locale) for locale in self._locales]
            )
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
                file = File(
                    id=f"wikipedia-{image.title}",
                    name=image.name,
                    path=image.path,
                    media_type=image.media_type,
                    links=[
                        Link(
                            StaticTranslations(
                                {
                                    locale: f"{image.wikimedia_commons_url}?uselang={locale}"
                                    for locale in self._locales
                                }
                            ),
                            label=_("Description, licensing, and image history"),
                            description=_(
                                "Find out more about this image on Wikimedia Commons."
                            ),
                            media_type=HTML,
                        )
                    ],
                    copyright_notice=self._copyright_notice,
                )
                self._image_files[image] = file
                self._ancestry.add(file)
            file_reference = FileReference(has_file_references, file)
            self._ancestry.add(file_reference)
            return file_reference
