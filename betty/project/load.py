"""
Provide the Ancestry loading API.
"""

from asyncio import gather
from xml.etree.ElementTree import Element

from html5lib import parse

from betty.ancestry.link import HasLinks, Link
from betty.cache.memory import MemoryCache
from betty.fetch import Fetcher, FetchError
from betty.locale.localizable import _, plain
from betty.media_type import InvalidMediaType, MediaType
from betty.project import Project, ProjectContext, ProjectEvent
from betty.user import User


class LoadAncestryEvent(ProjectEvent):
    """
    Dispatched to load ancestry data into a project.
    """


class PostLoadAncestryEvent(ProjectEvent):
    """
    Dispatched to postprocess ancestry data that was loaded into a project.

    This event is invoked immediately after :py:class:`betty.project.load.LoadAncestryEvent`.
    """


async def load(project: Project) -> None:
    """
    Load an ancestry.
    """
    async with project.app.user.message_progress(
        _("Loading ancestry...").format(
            output_directory=str(project.configuration.output_directory_path)
        )
    ) as progress:
        job_context = ProjectContext(
            project,
            cache=MemoryCache(),
            progress=progress,
        )
        await progress.add()
        await project.event_dispatcher.dispatch(
            LoadAncestryEvent(job_context), progress=progress
        )
        await project.event_dispatcher.dispatch(
            PostLoadAncestryEvent(job_context), progress=progress
        )
        await _fetch_link_titles(project, user=project.app.user)
        await progress.done()
        project.ancestry.immutable()


async def _fetch_link_titles(project: Project, *, user: User) -> None:
    await gather(
        *[
            _fetch_link_title(await project.app.fetcher, link, user=user)
            for entity in project.ancestry
            if isinstance(entity, HasLinks)
            for link in entity.links
        ]
    )


async def _fetch_link_title(fetcher: Fetcher, link: Link, *, user: User) -> None:
    if link.has_label:
        return
    try:
        response = await fetcher.fetch(link.url)
    except FetchError as error:
        await user.message_warning(error)
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

    document = parse(response.text)
    title = _extract_html_title(document)
    if title is not None:
        link.label = plain(title)
    if not link.description:
        description = _extract_html_meta_description(document)
        if description is not None:
            link.description = plain(description)


def _extract_html_title(document: Element) -> str | None:
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


def _extract_html_meta_description(document: Element) -> str | None:
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
