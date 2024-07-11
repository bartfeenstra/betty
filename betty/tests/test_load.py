import pytest
from aioresponses import aioresponses

from betty.app import App
from betty.load import load
from betty.model.ancestry import HasLinksEntity, Link
from betty.project import Project
from betty.tests.model.test___init__ import DummyEntity


class DummyHasLinks(HasLinksEntity, DummyEntity):
    pass


class TestLoad:
    async def test_should_fetch_link_with_unsupported_content_type(
        self,
        aioresponses: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"

        aioresponses.get(
            link_url,
            body="Hello, world!",
            headers={"Content-Type": "text/plain"},
        )

        link = Link(link_url)
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await load(project)

            assert link.label is None
            assert link.description is None

    @pytest.mark.parametrize(
        ("link_page_content_type"),
        [
            "text/html",
            "application/xhtml+xml",
        ],
    )
    async def test_should_fetch_link_with_invalid_html(
        self,
        link_page_content_type: str,
        aioresponses: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link_page_html = "<html></html>"

        aioresponses.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": link_page_content_type},
        )

        link = Link(link_url)
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await load(project)

            assert link.label is None
            assert link.description is None

    @pytest.mark.parametrize(
        ("link_page_content_type"),
        [
            "text/html",
            "application/xhtml+xml",
        ],
    )
    async def test_should_fetch_link_label_from_valid_html_with_title(
        self,
        link_page_content_type: str,
        aioresponses: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link_page_title = "Hello, world!"
        link_page_html = (
            f"<html><head><title>{link_page_title}</title></head><body></body></html>"
        )

        aioresponses.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": link_page_content_type},
        )

        link = Link(link_url)
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await load(project)

            assert link.label == link_page_title

    @pytest.mark.parametrize(
        ("link_page_content_type"),
        [
            "text/html",
            "application/xhtml+xml",
        ],
    )
    async def test_should_fetch_link_label_with_valid_html_without_title(
        self,
        link_page_content_type: str,
        aioresponses: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link_page_html = "<html><head></head><body></body></html>"

        aioresponses.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": link_page_content_type},
        )

        link = Link(link_url)
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await load(project)

            assert link.label is None

    @pytest.mark.parametrize(
        ("link_page_content_type", "meta_attr_name", "meta_attr_value"),
        [
            ("text/html", "name", "description"),
            ("application/xhtml+xml", "name", "description"),
            ("text/html", "property", "og:description"),
            ("application/xhtml+xml", "property", "og:description"),
        ],
    )
    async def test_should_fetch_link_description_from_valid_html_with_meta_description(
        self,
        link_page_content_type: str,
        meta_attr_name: str,
        meta_attr_value: str,
        aioresponses: aioresponses,
        new_temporary_app: App,
    ) -> None:
        link_url = "https://example.com"
        link_page_meta_description = "'Hello, world!' is a common internet greeting."
        link_page_html = f'<html><head><title>Hello, world!</title><meta {meta_attr_name}="{meta_attr_value}" content="{link_page_meta_description}"></head><body></body></html>'

        aioresponses.get(
            link_url,
            body=link_page_html,
            headers={"Content-Type": link_page_content_type},
        )

        link = Link(link_url)
        async with Project.new_temporary(new_temporary_app) as project:
            project.ancestry.add(DummyHasLinks(links=[link]))
            async with project:
                await load(project)

            assert link.description == link_page_meta_description
