import pytest
from multidict import CIMultiDict

from betty.ancestry.has_links import HasLinks
from betty.ancestry.link import Link
from betty.app import App
from betty.fetch import FetchResponse
from betty.fetch.static import StaticFetcher
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project
from betty.project.load import load
from betty.test_utils.conftest import NewTemporaryAppFactory
from betty.test_utils.model import DummyEntity


class DummyHasLinks(HasLinks, DummyEntity):
    pass


async def test_load__should_immutable_ancestry(new_temporary_app: App) -> None:
    async with Project.new_temporary(new_temporary_app) as project, project:
        await load(project)
        assert project.ancestry.is_immutable


async def test_load__should_fetch_link_with_unsupported_content_type(
    new_temporary_app_factory: NewTemporaryAppFactory,
) -> None:
    link_url = "https://example.com"
    link = Link(link_url)
    fetcher = StaticFetcher(
        fetch_map={
            link_url: FetchResponse(
                CIMultiDict({"Content-Type": "text/plain"}),
                b"Hello, world!",
                "utf-8",
            )
        }
    )
    async with (
        new_temporary_app_factory(fetcher=fetcher) as app,
        app,
        Project.new_temporary(app) as project,
    ):
        project.ancestry.add(DummyHasLinks(links=[link]))
        async with project:
            await load(project)

        assert not link.has_label
        assert not link.description


@pytest.mark.parametrize(
    ("link_page_content_type"),
    [
        "text/html",
        "application/xhtml+xml",
    ],
)
async def test_load__should_fetch_link_with_invalid_html(
    link_page_content_type: str,
    new_temporary_app_factory: NewTemporaryAppFactory,
) -> None:
    link_url = "https://example.com"
    link_page_html = "<html></html>"
    link = Link(link_url)
    fetcher = StaticFetcher(
        fetch_map={
            link_url: FetchResponse(
                CIMultiDict({"Content-Type": link_page_content_type}),
                link_page_html.encode("utf-8"),
                "utf-8",
            )
        }
    )
    async with (
        new_temporary_app_factory(fetcher=fetcher) as app,
        app,
        Project.new_temporary(app) as project,
    ):
        project.ancestry.add(DummyHasLinks(links=[link]))
        async with project:
            await load(project)

        assert not link.has_label
        assert not link.description


@pytest.mark.parametrize(
    ("link_page_content_type"),
    [
        "text/html",
        "application/xhtml+xml",
    ],
)
async def test_load__should_fetch_link_label_from_valid_html_with_title(
    link_page_content_type: str,
    new_temporary_app_factory: NewTemporaryAppFactory,
) -> None:
    link_url = "https://example.com"
    link_page_title = "Hello, world!"
    link_page_html = (
        f"<html><head><title>{link_page_title}</title></head><body></body></html>"
    )
    link = Link(link_url)
    fetcher = StaticFetcher(
        fetch_map={
            link_url: FetchResponse(
                CIMultiDict({"Content-Type": link_page_content_type}),
                link_page_html.encode("utf-8"),
                "utf-8",
            )
        }
    )
    async with (
        new_temporary_app_factory(fetcher=fetcher) as app,
        app,
        Project.new_temporary(app) as project,
    ):
        project.ancestry.add(DummyHasLinks(links=[link]))
        async with project:
            await load(project)

        assert link.label.localize(DEFAULT_LOCALIZER) == link_page_title


@pytest.mark.parametrize(
    ("link_page_content_type"),
    [
        "text/html",
        "application/xhtml+xml",
    ],
)
async def test_load__should_fetch_link_label_with_valid_html_without_title(
    link_page_content_type: str,
    new_temporary_app_factory: NewTemporaryAppFactory,
) -> None:
    link_url = "https://example.com"
    link_page_html = "<html><head></head><body></body></html>"
    link = Link(link_url)
    fetcher = StaticFetcher(
        fetch_map={
            link_url: FetchResponse(
                CIMultiDict({"Content-Type": "text/plain"}),
                link_page_html.encode("utf-8"),
                "utf-8",
            )
        }
    )
    async with (
        new_temporary_app_factory(fetcher=fetcher) as app,
        app,
        Project.new_temporary(app) as project,
    ):
        project.ancestry.add(DummyHasLinks(links=[link]))
        async with project:
            await load(project)

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
async def test_load__should_fetch_link_description_from_valid_html_with_meta_description(
    link_page_content_type: str,
    meta_attr_name: str,
    meta_attr_value: str,
    new_temporary_app_factory: NewTemporaryAppFactory,
) -> None:
    link_url = "https://example.com"
    link_page_meta_description = "'Hello, world!' is a common internet greeting."
    link_page_html = f'<html><head><title>Hello, world!</title><meta {meta_attr_name}="{meta_attr_value}" content="{link_page_meta_description}"></head><body></body></html>'
    link = Link(link_url)
    fetcher = StaticFetcher(
        fetch_map={
            link_url: FetchResponse(
                CIMultiDict({"Content-Type": link_page_content_type}),
                link_page_html.encode("utf-8"),
                "utf-8",
            )
        }
    )
    async with (
        new_temporary_app_factory(fetcher=fetcher) as app,
        app,
        Project.new_temporary(app) as project,
    ):
        project.ancestry.add(DummyHasLinks(links=[link]))
        async with project:
            await load(project)

        assert link.description is not None
        assert (
            link.description.localize(DEFAULT_LOCALIZER) == link_page_meta_description
        )
