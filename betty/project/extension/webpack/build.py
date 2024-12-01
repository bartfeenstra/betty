"""
Perform Webpack builds.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio import to_thread, gather, create_task
from json import dumps, loads
from logging import getLogger
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, final, Self

import aiofiles
from aiofiles.os import makedirs
from typing_extensions import override
from watchdog.events import LoggingEventHandler
from watchdog.observers import Observer

from betty import _npm
from betty.app.factory import AppDependentFactory
from betty.fs import ROOT_DIRECTORY_PATH
from betty.hashid import hashid, hashid_sequence, hashid_file_content
from betty.os import copy_tree
from betty.subprocess import run_process, console_args
from betty.typing import internal

if TYPE_CHECKING:
    from betty.project import Project
    from betty.app import App
    from betty.project.extension import Extension
    from betty.job import Context
    from betty.locale.localizer import Localizer
    from betty.render import Renderer
    from collections.abc import Sequence, MutableMapping
    from betty.project.extension.webpack import WebpackEntryPointProvider

_NPM_PROJECT_DIRECTORIES_PATH = Path(__file__).parent / "webpack"


# @todo move this to DirectoryBuilder?
async def _npm_project_id(
    entry_point_providers: Sequence[WebpackEntryPointProvider & Extension],
) -> str:
    return hashid_sequence(
        await hashid_file_content(_NPM_PROJECT_DIRECTORIES_PATH / "package.json"),
        *[
            await hashid_file_content(
                entry_point_provider.webpack_entry_point_directory_path()
                / "package.json"
            )
            for entry_point_provider in entry_point_providers
        ],
    )


# @todo move this to DirectoryBuilder?
async def _npm_project_directory_path(
    working_directory_path: Path,
    entry_point_providers: Sequence[WebpackEntryPointProvider & Extension],
) -> Path:
    return working_directory_path / await _npm_project_id(entry_point_providers)


# @todo move this to DirectoryBuilder?
def webpack_build_id(
    entry_point_providers: Sequence[WebpackEntryPointProvider & Extension], debug: bool
) -> str:
    """
    Generate the ID for a Webpack build.
    """
    return hashid_sequence(
        "true" if debug else "false",
        *(
            "-".join(
                map(
                    hashid,
                    entry_point_provider.webpack_entry_point_cache_keys(),
                )
            )
            for entry_point_provider in entry_point_providers
        ),
    )


# @todo move this to DirectoryBuilder?
def _webpack_build_directory_path(
    npm_project_directory_path: Path,
    entry_point_providers: Sequence[WebpackEntryPointProvider & Extension],
    debug: bool,
) -> Path:
    return (
        npm_project_directory_path
        / f"build-{webpack_build_id(entry_point_providers, debug)}"
    )


class _Builder:
    def __init__(
        self,
        npm_project_directory_path: Path,
        webpack_build_directory_path: Path,
        debug: bool,
    ) -> None:
        self._debug = debug
        self._npm_project_directory_path = npm_project_directory_path
        self._webpack_build_directory_path = webpack_build_directory_path

    async def _prepare_webpack_extension(
        self, npm_project_directory_path: Path
    ) -> None:
        await gather(
            *[
                to_thread(
                    copy2,
                    source_file_path,
                    npm_project_directory_path,
                )
                for source_file_path in (
                    _NPM_PROJECT_DIRECTORIES_PATH / "package.json",
                    _NPM_PROJECT_DIRECTORIES_PATH / "webpack.config.js",
                    ROOT_DIRECTORY_PATH / ".browserslistrc",
                    ROOT_DIRECTORY_PATH / "tsconfig.json",
                )
            ]
        )

    async def _prepare_working_directory(
        self,
        npm_project_directory_path: Path,
        webpack_build_directory_path: Path,
        *,
        workspace: WatchBuildWorkspace | None,
    ) -> None:
        npm_project_package_json_dependencies: MutableMapping[str, str] = {}
        webpack_entry: MutableMapping[str, str] = {}
        await makedirs(npm_project_directory_path, exist_ok=True)
        await gather(
            self._prepare_webpack_extension(npm_project_directory_path),
            self._do_prepare_working_directory(
                npm_project_directory_path,
                webpack_build_directory_path,
                npm_project_package_json_dependencies,
                webpack_entry,
                workspace=workspace,
            ),
        )
        webpack_configuration_json = dumps(
            {
                # Use a relative path so we avoid portability issues with
                # leading root slashes or drive letters.
                "buildDirectoryPath": str(
                    webpack_build_directory_path.relative_to(npm_project_directory_path)
                ),
                "debug": self._debug,
                "entry": webpack_entry,
                # @todo Should we split this out into subclasses?
                "workspaceProjectConfigurationFilePath": workspace.name()
                if workspace
                else None,
                "watchFiles": list(map(str, workspace.watch_files()))
                if workspace
                else [],
                # @todo Should we split this out into subclasses?
                # "staticDirectory":
            }
        )
        async with aiofiles.open(
            npm_project_directory_path / "webpack.config.json", "w"
        ) as configuration_f:
            await configuration_f.write(webpack_configuration_json)

        # Add dependencies to package.json.
        npm_project_package_json_path = npm_project_directory_path / "package.json"
        async with aiofiles.open(
            npm_project_package_json_path, "r"
        ) as npm_project_package_json_f:
            npm_project_package_json = loads(await npm_project_package_json_f.read())
        npm_project_package_json["dependencies"].update(
            npm_project_package_json_dependencies
        )
        async with aiofiles.open(
            npm_project_package_json_path, "w"
        ) as npm_project_package_json_f:
            await npm_project_package_json_f.write(dumps(npm_project_package_json))

    @abstractmethod
    async def _do_prepare_working_directory(
        self,
        npm_project_directory_path: Path,
        webpack_build_directory_path: Path,
        npm_project_package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
        *,
        workspace: WatchBuildWorkspace | None,
    ) -> None:
        pass

    async def _npm_install(self, npm_project_directory_path: Path) -> None:
        await _npm.npm(("install", "--production"), cwd=npm_project_directory_path)

    async def _prepare_build(
        self, *, workspace: WatchBuildWorkspace | None
    ) -> tuple[Path, Path]:
        if self._webpack_build_directory_path.exists():
            return self._npm_project_directory_path, self._webpack_build_directory_path
        npm_install_required = not self._npm_project_directory_path.exists()
        await self._prepare_working_directory(
            self._npm_project_directory_path,
            self._webpack_build_directory_path,
            workspace=workspace,
        )
        if npm_install_required:
            await self._npm_install(self._npm_project_directory_path)

        # Ensure there is always a vendor.css. This makes for easy and unconditional importing.
        await makedirs(self._webpack_build_directory_path / "css", exist_ok=True)
        await to_thread(
            (self._webpack_build_directory_path / "css" / "vendor.css").touch
        )

        return self._npm_project_directory_path, self._webpack_build_directory_path


@internal
@final
class DirectoryBuilder(_Builder):
    """
    Produce a Webpack build in a specific directory.
    """

    def __init__(
        self,
        npm_project_directory_path: Path,
        webpack_build_directory_path: Path,
        debug: bool,
        entry_point_providers: Sequence[WebpackEntryPointProvider & Extension],
        renderer: Renderer,
        *,
        job_context: Context,
        localizer: Localizer,
    ) -> None:
        super().__init__(
            npm_project_directory_path, webpack_build_directory_path, debug
        )
        self._entry_point_providers = entry_point_providers
        self._renderer = renderer
        self._job_context = job_context
        self._localizer = localizer

    @classmethod
    async def new(
        cls,
        working_directory_path: Path,
        debug: bool,
        entry_point_providers: Sequence[WebpackEntryPointProvider & Extension],
        renderer: Renderer,
        *,
        job_context: Context,
        localizer: Localizer,
    ) -> Self:
        """
        Create a new instance.
        """
        npm_project_directory_path = await _npm_project_directory_path(
            working_directory_path, entry_point_providers
        )
        return cls(
            npm_project_directory_path,
            _webpack_build_directory_path(
                npm_project_directory_path, entry_point_providers, debug
            ),
            debug,
            entry_point_providers,
            renderer,
            job_context=job_context,
            localizer=localizer,
        )

    async def build(self, *, watch: bool = False) -> Path:
        """
        Build the Webpack assets.

        :return: The path to the directory from which the assets can be copied to their
            final destination.
        """
        (
            npm_project_directory_path,
            webpack_build_directory_path,
        ) = await self._prepare_build(workspace=None)

        if watch:
            webpack_task = create_task(
                run_process(
                    [*console_args(), "npm", "run", "build-watch"],
                    cwd=npm_project_directory_path,
                    shell=True,
                )
            )
            try:
                # @todo Finish this
                pass
            finally:
                webpack_task.cancel()
        else:
            await _npm.npm(("run", "build"), cwd=npm_project_directory_path)
        getLogger(__name__).info(
            self._localizer._("Built the Webpack front-end assets.")
        )
        return webpack_build_directory_path

    @override
    async def _do_prepare_working_directory(
        self,
        npm_project_directory_path: Path,
        webpack_build_directory_path: Path,
        npm_project_package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
        *,
        workspace: WatchBuildWorkspace | None,
    ) -> None:
        await gather(
            *(
                self._prepare_webpack_entry_point_provider(
                    npm_project_directory_path,
                    type(entry_point_provider),
                    npm_project_package_json_dependencies,
                    webpack_entry,
                )
                for entry_point_provider in self._entry_point_providers
            ),
        )

    async def _prepare_webpack_entry_point_provider(
        self,
        npm_project_directory_path: Path,
        entry_point_provider: type[WebpackEntryPointProvider & Extension],
        npm_project_package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
    ) -> None:
        entry_point_provider_working_directory_path = (
            npm_project_directory_path
            / "entry_points"
            / entry_point_provider.plugin_id()
        )
        await copy_tree(
            entry_point_provider.webpack_entry_point_directory_path(),
            entry_point_provider_working_directory_path,
            file_callback=lambda destination_file_path: self._renderer.render_file(
                destination_file_path,
                job_context=self._job_context,
                localizer=self._localizer,
            ),
        )
        npm_project_package_json_dependencies[entry_point_provider.plugin_id()] = (
            # Ensure a relative path inside the npm project directory, or else npm
            # will not install our entry points' dependencies.
            f"file:{entry_point_provider_working_directory_path.relative_to(npm_project_directory_path)}"
        )
        # Webpack requires relative paths to start with a leading dot and use forward slashes.
        webpack_entry[entry_point_provider.plugin_id()] = "/".join(
            (
                ".",
                *(entry_point_provider_working_directory_path / "main.ts")
                .relative_to(npm_project_directory_path)
                .parts,
            )
        )


@internal
@final
class WatchBuilder(_Builder):
    """
    Build and serve a workspace, and watch for changes.
    """

    def __init__(self, workspace: WatchBuildWorkspace, project: Project) -> None:
        super().__init__(
            project.configuration.project_directory_path / "npm",
            project.configuration.project_directory_path / "npm" / "webpack",
            True,
        )
        self._workspace = workspace
        self._project = project

    async def build(self) -> None:
        """
        Build the Webpack assets continuously.
        """
        await self._workspace.pre_build(self._project)
        async with self._project:
            npm_project_directory_path, _ = await self._prepare_build(
                workspace=self._workspace
            )
            webpack_task = create_task(
                run_process(
                    [*console_args(), "npm", "run", "build-watch"],
                    cwd=npm_project_directory_path,
                    shell=True,
                )
            )
            try:
                event_handler = LoggingEventHandler(logger=logging.getLogger(__name__))
                for watch_file in self._workspace.watch_files():
                    observer = Observer()
                    observer.schedule(event_handler, str(watch_file), recursive=True)
                    observer.start()

                while True:
                    await asyncio.sleep(999)
            finally:
                webpack_task.cancel()

    @override
    async def _do_prepare_working_directory(
        self,
        npm_project_directory_path: Path,
        webpack_build_directory_path: Path,
        npm_project_package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
        *,
        workspace: WatchBuildWorkspace | None,
    ) -> None:
        # @todo Finish this
        pass


class WatchBuildWorkspace(AppDependentFactory, ABC):
    """
    A Webpack watch build workspace.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @classmethod
    def name(cls) -> str:
        """
        Get the workspace's fully qualified name.

        The returned value is importable using :py:func:`betty.importlib.import_any`.
        """
        return f"{cls.__module__}:{cls.__name__}"

    # @todo This is only useful if we are to subsequently allow the Python code here to rebuild.
    # @todo
    # @todo
    # @todo
    @abstractmethod
    def watch_files(self) -> set[Path]:
        """
        Get the paths to the files and directories to watch.
        """
        pass

    @abstractmethod
    async def pre_build(self, project: Project) -> None:
        """
        Configure and prepare the project (workspace) before the build.

        The project has not bootstrapped yet, and may be reconfigured.
        """
        pass
