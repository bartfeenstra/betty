"""
Perform Webpack builds.
"""

from __future__ import annotations


import asyncio
import logging
from abc import abstractmethod
from asyncio import (
    to_thread,
    gather,
    create_task,
    get_running_loop,
    run_coroutine_threadsafe,
    AbstractEventLoop,
)
from json import dumps, loads
from logging import getLogger
from pathlib import Path
from shutil import copy2, copytree
from typing import TYPE_CHECKING, final, Sequence

import aiofiles
from aiofiles.os import makedirs
from typing_extensions import override
from watchdog.events import (
    FileSystemEventHandler,
    DirMovedEvent,
    FileMovedEvent,
    DirCreatedEvent,
    FileCreatedEvent,
    DirDeletedEvent,
    FileDeletedEvent,
    DirModifiedEvent,
    FileModifiedEvent,
)
from watchdog.observers import Observer

from betty import _npm, fs
from betty._npm import NpmUnavailable
from betty.fs import ROOT_DIRECTORY_PATH
from betty.hashid import hashid, hashid_sequence, hashid_file_content
from betty.os import copy_tree
from betty.project import Project
from betty.project.extension import Extension, EXTENSION_REPOSITORY
from betty.subprocess import run_process_in_terminal
from betty.typing import internal
from betty.app import App

if TYPE_CHECKING:
    from betty.event_dispatcher import EventHandlerRegistry
    from collections.abc import Sequence, MutableMapping, Awaitable, Callable

_WEBPACK_EXTENSION_WEBPACK_DIRECTORY_PATH = Path(__file__).parent / "webpack"


@internal
class EntryPointProvider(Extension):
    """
    An extension that provides Webpack entry points.

    Any extensions extending this MUST NOT also register event handlers. In a situation where it appears a single
    extension must integrate with Webpack and register event handlers, split the functionality into separate extensions
    and declare dependencies and order using :py:meth:`betty.project.extension.Extension.depends_on` and
    :py:meth:`betty.project.extension.Extension.depended_on_by`.
    """

    @classmethod
    @abstractmethod
    def webpack_entry_point_directory_path(cls) -> Path:
        """
        Get the path to the directory with the entry point assets.

        The directory must include at least a ``package.json`` and ``main.ts``.
        """
        pass

    @abstractmethod
    async def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        """
        Get the keys that make a Webpack build for this provider unique.

        Providers that can be cached regardless may ``return ()``.
        """
        pass

    @final
    @override
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        pass


async def _get_entry_point_providers(
    project: Project,
) -> Sequence[EntryPointProvider & Extension]:
    extensions = await project.extensions
    return [
        extension
        for extension in extensions.flatten()
        if isinstance(extension, EntryPointProvider)
    ]


async def get_prebuilt_build_directory_path(project: Project) -> Path:
    """
    Get the path to a prebuilt Webpack build.
    """
    return (
        fs.PREBUILT_ASSETS_DIRECTORY_PATH
        / "webpack"
        / f"build-{await get_build_id(project)}"
    )


async def get_build_id(project: Project) -> str:
    """
    Generate the ID for a Webpack build.
    """
    return hashid_sequence(
        "true" if project.configuration.debug else "false",
        await hashid_file_content(
            _WEBPACK_EXTENSION_WEBPACK_DIRECTORY_PATH / "package.json"
        ),
        *[
            "-".join(
                [
                    await hashid_file_content(
                        entry_point_provider.webpack_entry_point_directory_path()
                        / "package.json"
                    ),
                    *map(
                        hashid,
                        await entry_point_provider.webpack_entry_point_cache_keys(),
                    ),
                ]
            )
            for entry_point_provider in await _get_entry_point_providers(project)
        ],
    )


async def prebuild() -> Path:
    """
    Prebuild the Webpack assets.
    """
    async with App.new_temporary() as app, app, Project.new_temporary(app) as project:
        project.configuration.extensions.enable(
            *await EXTENSION_REPOSITORY.select(
                EntryPointProvider  # type: ignore[type-abstract]
            )
        )
        async with project:
            output_directory_path = await get_prebuilt_build_directory_path(project)
            builder = Builder(project)
            await builder.build(output_directory_path)
    return output_directory_path


class _EntryPointEventHandler(FileSystemEventHandler):
    """
    Respond to changes in a Webpack entry point's directory by copying the files to the working directory.
    """

    def __init__(
        self, callback: Callable[[], Awaitable[None]], loop: AbstractEventLoop
    ):
        self._callback = callback
        self._loop = loop

    def _handle(self) -> None:
        # @todo - Limit how often we even run this (types of events, maybe a delay?)
        # @todo - Allow callbacks to be cancelled. But how?
        # @todo
        # @todo
        run_coroutine_threadsafe(self._callback(), self._loop)

    @override
    def on_moved(self, event: DirMovedEvent | FileMovedEvent) -> None:
        self._handle()

    @override
    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        self._handle()

    @override
    def on_deleted(self, event: DirDeletedEvent | FileDeletedEvent) -> None:
        self._handle()

    @override
    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        self._handle()


@internal
@final
class Builder:
    """
    Build Webpack assets.
    """

    def __init__(self, project: Project) -> None:
        self._project = project

    async def build(
        self, output_directory_path: Path | None = None, *, watch: bool = False
    ) -> None:
        """
        Build the Webpack assets.
        """
        if output_directory_path is None:
            output_directory_path = self._project.configuration.output_directory_path
        if watch:
            await self._build_watch(output_directory_path)
        else:
            await self._build(output_directory_path)

    async def _build(self, output_directory_path: Path) -> None:
        try:
            # (Re)build the assets if npm is available.
            await self._prepare(output_directory_path, watch=False)
            await _npm.npm(("run", "build"), cwd=await self._working_directory_path())
        except NpmUnavailable:
            # Use prebuilt assets if they exist.
            prebuilt_build_directory_path = await get_prebuilt_build_directory_path(
                self._project
            )
            if not prebuilt_build_directory_path.exists():
                raise
            copytree(
                prebuilt_build_directory_path,
                output_directory_path,
            )

        localizer = await self._project.app.localizer
        getLogger(__name__).info(localizer._("Built the Webpack front-end assets."))

    async def _build_watch(self, output_directory_path: Path) -> None:
        await self._prepare(output_directory_path, watch=True)
        webpack_task = create_task(
            run_process_in_terminal(
                ["npm", "run", "watch"], cwd=await self._working_directory_path()
            )
        )
        try:
            while not webpack_task.done():
                await asyncio.sleep(0)
        finally:
            webpack_task.cancel()

    async def _working_directory_path(self) -> Path:
        return (
            self._project.app.binary_file_cache.with_scope("webpack")
            .with_scope(await get_build_id(self._project))
            .path
        )

    async def _prepare_webpack_extension(self) -> None:
        await gather(
            *[
                to_thread(
                    copy2,
                    source_file_path,
                    await self._working_directory_path(),
                )
                for source_file_path in (
                    _WEBPACK_EXTENSION_WEBPACK_DIRECTORY_PATH / "package.json",
                    _WEBPACK_EXTENSION_WEBPACK_DIRECTORY_PATH / "webpack.config.js",
                    ROOT_DIRECTORY_PATH / ".browserslistrc",
                    ROOT_DIRECTORY_PATH / "tsconfig.json",
                )
            ]
        )

    async def _prepare_webpack_entry_point_provider(
        self,
        entry_point_provider: type[EntryPointProvider & Extension],
        package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
        *,
        watch: bool,
    ) -> None:
        working_directory_path = await self._working_directory_path()
        entry_point_provider_working_directory_path = (
            working_directory_path / "entry_points" / entry_point_provider.plugin_id()
        )

        package_json_dependencies[entry_point_provider.plugin_id()] = (
            # Ensure a relative path inside the npm project directory, or else npm
            # will not install our entry points' dependencies.
            f"file:{entry_point_provider_working_directory_path.relative_to(working_directory_path)}"
        )
        # Webpack requires relative paths to start with a leading dot and use forward slashes.
        webpack_entry[entry_point_provider.plugin_id()] = "/".join(
            (
                ".",
                *(entry_point_provider_working_directory_path / "main.ts")
                .relative_to(working_directory_path)
                .parts,
            )
        )

        if watch:
            event_handler = _EntryPointEventHandler(
                lambda: self._copy_entry_point_provider(
                    entry_point_provider, entry_point_provider_working_directory_path
                ),
                get_running_loop(),
            )
            observer = Observer()
            observer.schedule(
                event_handler,
                str(entry_point_provider.webpack_entry_point_directory_path()),
                recursive=True,
            )
            observer.start()

        await self._copy_entry_point_provider(
            entry_point_provider, entry_point_provider_working_directory_path
        )

    async def _copy_entry_point_provider(
        self,
        entry_point_provider: type[EntryPointProvider & Extension],
        entry_point_provider_working_directory_path: Path,
    ) -> None:
        localizer = await self._project.app.localizer
        renderer = await self._project.renderer
        await copy_tree(
            entry_point_provider.webpack_entry_point_directory_path(),
            entry_point_provider_working_directory_path,
            file_callback=lambda destination_file_path: renderer.render_file(
                destination_file_path, localizer=localizer
            ),
        )

    async def _prepare_working_directory(
        self, output_directory_path: Path, *, watch: bool
    ) -> None:
        working_directory_path = await self._working_directory_path()
        package_json_dependencies: MutableMapping[str, str] = {}
        webpack_entry: MutableMapping[str, str] = {}
        await makedirs(working_directory_path, exist_ok=True)
        await gather(
            self._prepare_webpack_extension(),
            *(
                self._prepare_webpack_entry_point_provider(
                    type(entry_point_provider),
                    package_json_dependencies,
                    webpack_entry,
                    watch=watch,
                )
                for entry_point_provider in await _get_entry_point_providers(
                    self._project
                )
            ),
        )
        webpack_configuration_json = dumps(
            {
                "outputDirectoryPath": str(output_directory_path.resolve()),
                "debug": self._project.configuration.debug,
                "entry": webpack_entry,
            }
        )
        async with aiofiles.open(
            working_directory_path / "webpack.config.json", "w"
        ) as configuration_f:
            await configuration_f.write(webpack_configuration_json)

        # Add dependencies to package.json.
        package_json_path = working_directory_path / "package.json"
        async with aiofiles.open(package_json_path, "r") as package_json_f:
            package_json = loads(await package_json_f.read())
        package_json["dependencies"].update(package_json_dependencies)
        async with aiofiles.open(package_json_path, "w") as package_json_f:
            await package_json_f.write(dumps(package_json))

    async def _prepare(self, output_directory_path: Path, *, watch: bool) -> None:
        logger = logging.getLogger(__name__)
        working_directory_path = await self._working_directory_path()
        logger.debug(f"Building Webpack assets in {working_directory_path}...")
        logger.debug(f"Outputting Webpack assets to {output_directory_path}...")
        npm_install_required = not (
            working_directory_path / "package-lock.json"
        ).exists()
        await self._prepare_working_directory(output_directory_path, watch=watch)
        if npm_install_required:
            await _npm.npm(("install", "--production"), cwd=working_directory_path)

        # Ensure there is always a vendor.css. This makes for easy and unconditional importing.
        await makedirs(output_directory_path / "www" / "css", exist_ok=True)
        await to_thread((output_directory_path / "www" / "css" / "vendor.css").touch)
