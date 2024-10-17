"""
Tools to serve demonstration sites.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import AsyncExitStack
from shutil import rmtree
from typing import final, TYPE_CHECKING

from typing_extensions import override

from betty import serve
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import load, generate
from betty.project.extension.demo.project import create_project
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError

if TYPE_CHECKING:
    from betty.app import App


@final
class DemoServer(Server):
    """
    Serve the Betty demonstration site.
    """

    def __init__(self, app: App):
        super().__init__(localizer=DEFAULT_LOCALIZER)
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
            await load.load(project)
            if not project_directory_path.is_dir():
                try:
                    await generate.generate(project)
                except BaseException:
                    # Ensure that we never leave a partial build.
                    await to_thread(rmtree, project_directory_path)
                    raise
            self._server = await serve.BuiltinProjectServer.new_for_project(project)
            await self._exit_stack.enter_async_context(self._server)
        except BaseException:
            # __aexit__() is not called when __aenter__() raises an exception, so ensure we clean up our resources.
            await self.stop()
            raise

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
