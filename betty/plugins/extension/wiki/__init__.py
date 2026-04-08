"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

from asyncio import gather
from typing import Self, final, override

from betty.extension import Extension, ExtensionDefinition
from betty.plugins.copyright_notice.wikipedia_contributors import WikipediaContributors
from betty.project import Project
from betty.service.factory import Manufacturable
from betty.service.provider import ServiceProvider, service
from betty.wiki import populator as populator_api
from betty.wiki.client import Client


@final
@ExtensionDefinition("wiki", label="Wiki")
class Wiki(Extension, ServiceProvider, Manufacturable):
    """
    .. plugin:: extension:wiki.
    """

    def __init__(self, *, project: Project):
        super().__init__(services=project)
        self._project = project

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project=project)

    @service
    async def client(self) -> Client:
        """
        The API client.
        """
        return Client(
            download_directory_path=self._project.upstream.binary_file_cache.with_scope(
                "wiki-client"
            ).path,
            http_client=await self._project.upstream.http_client,
            user=self._project.upstream.user,
        )

    @service
    async def populator(self) -> populator_api.Populator:
        """
        The ancestry populator.
        """
        copyright_notice, http_client, localizers = await gather(
            self._project.factory.new(WikipediaContributors),
            self.client,
            self._project.localizers,
        )
        return populator_api.Populator(
            self._project.ancestry,
            list(self._project.locales.keys()),
            localizers,
            http_client,
            copyright_notice,
            user=self._project.upstream.user,
        )
