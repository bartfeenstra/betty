"""Integrate Betty with `Wikipedia <https://wikipedia.org>`_."""

from __future__ import annotations

from asyncio import gather
from typing import Self, final, override

from betty.copyright_notices.wikipedia_contributors import WikipediaContributors
from betty.factory import new
from betty.project import Project
from betty.service_provider import ServiceProvider, ServiceProviderDefinition
from betty.services.simple import service
from betty.wiki import populator as populator_api
from betty.wiki.client import Client


@final
@ServiceProviderDefinition("wiki", label="Wiki")
class Wiki(ServiceProvider[Project]):
    """
    .. plugin:: service-provider:wiki.
    """

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(services=project)

    @service
    async def client(self) -> Client:
        """
        The API client.
        """
        return Client(
            download_directory=self.services.upstream.binary_file_cache.with_scope(
                "wiki-client"
            ).directory,
            http_client=await self.services.upstream.http_client,
            user=self.services.upstream.user,
        )

    @service
    async def populator(self) -> populator_api.Populator:
        """
        The ancestry populator.
        """
        copyright_notice, http_client = await gather(
            new(WikipediaContributors, self.services), self.client
        )
        return populator_api.Populator(
            self.services.ancestry,
            list(self.services.locales.keys()),
            self.services.localizers,
            http_client,
            copyright_notice,
            user=self.services.upstream.user,
        )
