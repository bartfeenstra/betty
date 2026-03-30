from __future__ import annotations

from typing import TYPE_CHECKING

from betty.load import load
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.enricher.populate_links import PopulateLinks
from betty.plugins.entity.link import Link

if TYPE_CHECKING:
    from aioresponses import aioresponses

    from betty.test_utils.conftest import IsolatedProjectFactory


class TestPopulateLinks:
    async def test_enrich(
        self,
        http_client_mock: aioresponses,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:

        link_url = "https://example.com"
        link_page_title = "Hello, world!"
        link_page_html = (
            f"<html><head><title>{link_page_title}</title></head><body></body></html>"
        )
        http_client_mock.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": "text/html"},
        )

        async with isolated_project_factory(enrichers=[PopulateLinks]) as project:
            link = Link("https://example.com")
            project.ancestry.add(link)
            await load(project)
            assert link.label.localize(DEFAULT_LOCALIZER) == link_page_title
