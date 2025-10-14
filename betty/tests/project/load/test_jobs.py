import pytest
from aioresponses import aioresponses

from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.app import App
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project, ProjectContext
from betty.project.load.jobs import PopulateLink
from betty.test_utils.job import do


class DummyHasLinks(HasLinks):
    pass


class TestPopulateLink:
    async def test_do__should_fetch_link_with_unsupported_content_type(
        self,
        http_client_mock: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link = Link(link_url)
        http_client_mock.get(
            link_url,
            body=b"Hello, world!",
            headers={
                "Content-Type": "text/plain",
            },
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await do(ProjectContext(project), PopulateLink(link))

            assert not link.has_label
            assert not link.description

    @pytest.mark.parametrize(
        ("link_page_content_type"),
        [
            "text/html",
            "application/xhtml+xml",
        ],
    )
    async def test_do__should_fetch_link_with_invalid_html(
        self,
        link_page_content_type: str,
        http_client_mock: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link_page_html = "<html></html>"
        link = Link(link_url)
        http_client_mock.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": link_page_content_type},
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await do(ProjectContext(project), PopulateLink(link))

            assert not link.has_label
            assert not link.description

    @pytest.mark.parametrize(
        ("link_page_content_type"),
        [
            "text/html",
            "application/xhtml+xml",
        ],
    )
    async def test_do__should_fetch_link_label_from_valid_html_with_title(
        self,
        link_page_content_type: str,
        http_client_mock: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link_page_title = "Hello, world!"
        link_page_html = (
            f"<html><head><title>{link_page_title}</title></head><body></body></html>"
        )
        link = Link(link_url)
        http_client_mock.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": link_page_content_type},
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await do(ProjectContext(project), PopulateLink(link))

            assert link.label.localize(DEFAULT_LOCALIZER) == link_page_title

    @pytest.mark.parametrize(
        ("link_page_content_type"),
        [
            "text/html",
            "application/xhtml+xml",
        ],
    )
    async def test_do__should_fetch_link_label_with_valid_html_without_title(
        self,
        link_page_content_type: str,
        http_client_mock: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link_page_html = "<html><head></head><body></body></html>"
        link = Link(link_url)
        http_client_mock.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": link_page_content_type},
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await do(ProjectContext(project), PopulateLink(link))

            assert not link.has_label

    @pytest.mark.parametrize(
        ("link_page_content_type", "meta_attr_name", "meta_attr_value"),
        [
            ("text/html", "name", "description"),
            ("application/xhtml+xml", "name", "description"),
            ("text/html", "property", "og:description"),
            ("application/xhtml+xml", "property", "og:description"),
        ],
    )
    async def test_do__should_fetch_link_description_from_valid_html_with_meta_description(
        self,
        link_page_content_type: str,
        meta_attr_name: str,
        meta_attr_value: str,
        http_client_mock: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link_page_meta_description = "'Hello, world!' is a common internet greeting."
        link_page_html = f'<html><head><title>Hello, world!</title><meta {meta_attr_name}="{meta_attr_value}" content="{link_page_meta_description}"></head><body></body></html>'
        link = Link(link_url)
        http_client_mock.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": link_page_content_type},
        )
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await do(ProjectContext(project), PopulateLink(link))

            assert link.description is not None
            assert (
                link.description.localize(DEFAULT_LOCALIZER)
                == link_page_meta_description
            )
