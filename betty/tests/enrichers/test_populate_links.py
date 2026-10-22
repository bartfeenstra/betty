from __future__ import annotations

from typing import TYPE_CHECKING

from betty.enrichers.populate_links import PopulateLinks
from betty.entities.link import Link
from betty.load import load
from betty.localizer import default_localizer
from betty.project import Project

if TYPE_CHECKING:
    from aioresponses import aioresponses

    from betty.test_utils.conftest import NewIsolatedProject


class TestPopulateLinks:
    async def test_enrich(
        self,
        http_client_mock: aioresponses,
        new_isolated_project: NewIsolatedProject,
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

        async with new_isolated_project() as project:
            Project.enrichers.add_init_plugins(project, PopulateLinks)
            async with project:
                link = Link("https://example.com")
                project.ancestry.add(link)
                await load(project)
                assert link.label.localize(default_localizer) == link_page_title
