"""
Tools to serve demonstration sites.
"""

from __future__ import annotations

from asyncio import to_thread, Task, create_task
from contextlib import AsyncExitStack
from shutil import rmtree
from typing import final, TYPE_CHECKING

from typing_extensions import override

from betty import serve
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import load, generate, Project
from betty.project.extension.demo.project import create_project
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError

if TYPE_CHECKING:
    from betty.app import App


@final
class DemoServer(Server):
    """
    Serve the Betty demonstration site.
    """

    def __init__(self, app: App, *, watch: bool = False):
        super().__init__(localizer=DEFAULT_LOCALIZER)
        self._app = app
        self._watch = watch
        self._server: Server | None = None
        self._exit_stack = AsyncExitStack()
        self._generate_task: Task[None] | None = None

    @override
    @property
    def public_url(self) -> str:
        if self._server is not None:
            return self._server.public_url
        raise NoPublicUrlBecauseServerNotStartedError()

    async def _generate(self, project: Project) -> None:
        try:
            await generate.generate(project, watch=self._watch)
        except BaseException:
            # Ensure that we never leave a partial build.
            await to_thread(rmtree, project.configuration.output_directory_path)
            raise

    @override
    async def start(self) -> None:
        project_directory_path = self._app.binary_file_cache.with_scope("demo").path
        project = await create_project(self._app, project_directory_path)
        await self._exit_stack.enter_async_context(project)
        try:
            await load.load(project)
            if not project_directory_path.is_dir() or self._watch:
                self._generate_task = create_task(self._generate(project))
                self._exit_stack.callback(self._generate_task.cancel)
            self._server = await serve.BuiltinProjectServer.new_for_project(project)
            await self._exit_stack.enter_async_context(self._server)
        except BaseException:
            # __aexit__() is not called when __aenter__() raises an exception, so ensure we clean up our resources.
            await self.stop()
            raise

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()
