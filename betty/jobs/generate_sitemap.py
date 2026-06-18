"""
Jobs to generate sitemaps.
"""

from __future__ import annotations

from asyncio import to_thread
from typing import TYPE_CHECKING, Final, final, override

from betty.file import write
from betty.job import Job
from betty.media_types.html import HTML

if TYPE_CHECKING:
    from collections.abc import MutableSequence

    from betty.job.scheduler import Scheduler
    from betty.project import Project


@final
class GenerateSitemap(Job):
    """
    Generate a site's sitemap.
    """

    _sitemap_url_template: Final[str] = """<url>
        <loc>{{{ loc }}}</loc>
        <lastmod>{{{ lastmod }}}</lastmod>
    </url>
    """

    _sitemap_batch_template: Final[str] = """<?xml version="1.0" encoding="utf-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
        {{{ urls }}}
    </urlset>
    """

    _sitemap_sitemap_template: Final[str] = """<sitemap>
        <loc>{{{ loc }}}</loc>
    </sitemap>
    """

    _sitemap_template: Final[str] = """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        {{{ sitemaps }}}
    </sitemapindex>
    """

    def __init__(self, *, project: Project):
        super().__init__(self.id_for())
        self._project = project

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "generate-sitemap"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        context = scheduler.context

        url_generator = await self._project.url_generator

        await to_thread(
            self._project.www_directory.mkdir,
            exist_ok=True,
            parents=True,
        )

        sitemap_batches = []
        sitemap_batch_urls: MutableSequence[str] = []
        sitemap_batch_urls_length = 0
        sitemap_batches.append(sitemap_batch_urls)
        for locale in self._project.locales.keys():  # noqa: SIM118
            for entity in self._project.ancestry:
                if not entity.id.persistent:
                    continue
                if not entity.plugin().public_facing:
                    continue

                sitemap_batch_urls.append(
                    url_generator.generate(
                        entity,
                        absolute=True,
                        locale=locale,
                        media_type=HTML,
                    )
                )
                sitemap_batch_urls_length += 1

                if sitemap_batch_urls_length == 50_000:
                    sitemap_batch_urls = []
                    sitemap_batch_urls_length = 0
                    sitemap_batches.append(sitemap_batch_urls)

        sitemap_urls = []
        for sitemap_batch_index, sitemap_batch_urls in enumerate(sitemap_batches):
            sitemap_urls.append(
                url_generator.generate(
                    f"betty-static:///sitemap-{sitemap_batch_index}.xml",
                    absolute=True,
                )
            )
            rendered_sitemap_batch = self._sitemap_batch_template.replace(
                "{{{ urls }}}",
                "".join(
                    self._sitemap_url_template.replace(
                        "{{{ loc }}}", sitemap_batch_url
                    ).replace("{{{ lastmod }}}", context.start.isoformat())
                    for sitemap_batch_url in sitemap_batch_urls
                ),
            )
            await write(
                self._project.www_directory / f"sitemap-{sitemap_batch_index}.xml",
                rendered_sitemap_batch,
            )

        rendered_sitemap = self._sitemap_template.replace(
            "{{{ sitemaps }}}",
            "".join(
                self._sitemap_sitemap_template.replace("{{{ loc }}}", sitemap_url)
                for sitemap_url in sitemap_urls
            ),
        )
        await write(self._project.www_directory / "sitemap.xml", rendered_sitemap)
