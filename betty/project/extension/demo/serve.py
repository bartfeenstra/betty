"""
Tools to serve demonstration sites.
"""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty import serve
from betty.cache.memory import MemoryCache
from betty.locale.localizable import _
from betty.project import ProjectContext
from betty.project.extension.demo import generate_with_cleanup
from betty.project.extension.demo.project import create_project
from betty.serve import NoPublicUrlBecauseServerNotStartedError, Server

if TYPE_CHECKING:
    from betty.app import App


@final
class DemoServer(Server):
    """
    Serve the Betty demonstration site.
    """

    def __init__(self, app: App):
        super().__init__(user=app.user)
        self._app = app
        self._server: Server | None = None
        self._exit_stack = AsyncExitStack()

    @override
    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    @override
    async def start(self) -> None:
        project_directory_path = self._app.binary_file_cache.with_scope("demo").path
        project = await create_project(self._app, project_directory_path)
        await self._exit_stack.enter_async_context(project)

        try:
            async with project.app.user.message_progress(
                _("Generating site...")
            ) as progress:
                job_context = ProjectContext(
                    project, cache=MemoryCache(), progress=progress
                )
                await generate_with_cleanup(project, job_context=job_context)
            self._server = await serve.BuiltinProjectServer.new_for_project(project)
            await self._exit_stack.enter_async_context(self._server)
        except BaseException:
            # __aexit__() is not called when __aenter__() raises an exception, so ensure we clean up our resources.
            await self.stop()
            raise

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
