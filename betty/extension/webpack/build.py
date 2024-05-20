"""
Perform Webpack builds.
"""

from __future__ import annotations

from asyncio import to_thread
from json import dumps, loads
from logging import getLogger
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs

from betty import _npm
from betty.asyncio import gather
from betty.fs import ROOT_DIRECTORY_PATH, iterfiles
from betty.hashid import hashid, hashid_sequence, hashid_file_content

if TYPE_CHECKING:
    from betty.app.extension import Extension
    from betty.job import Context
    from betty.locale import Localizer
    from betty.render import Renderer
    from collections.abc import Sequence, MutableMapping
    from betty.extension.webpack import WebpackEntrypointProvider


_NPM_PROJECT_DIRECTORIES_PATH = Path(__file__).parent / "webpack"


async def _npm_project_id(
    entrypoint_providers: Sequence[WebpackEntrypointProvider & Extension], debug: bool
) -> str:
    return hashid_sequence(
        "true" if debug else "false",
        await hashid_file_content(_NPM_PROJECT_DIRECTORIES_PATH / "package.json"),
        *[
            await hashid_file_content(
                entrypoint_provider.webpack_entrypoint_directory_path() / "package.json"
            )
            for entrypoint_provider in entrypoint_providers
        ],
    )


async def _npm_project_directory_path(
    working_directory_path: Path,
    entrypoint_providers: Sequence[WebpackEntrypointProvider & Extension],
    debug: bool,
) -> Path:
    return working_directory_path / await _npm_project_id(entrypoint_providers, debug)


def webpack_build_id(
    entrypoint_providers: Sequence[WebpackEntrypointProvider & Extension],
) -> str:
    """
    Generate the ID for a Webpack build.
    """
    return hashid_sequence(
        *(
            "-".join(
                map(
                    hashid,
                    entrypoint_provider.webpack_entrypoint_cache_keys(),
                )
            )
            for entrypoint_provider in entrypoint_providers
        )
    )


def _webpack_build_directory_path(
    npm_project_directory_path: Path,
    entrypoint_providers: Sequence[WebpackEntrypointProvider & Extension],
) -> Path:
    return (
        npm_project_directory_path / f"build-{webpack_build_id(entrypoint_providers)}"
    )


class Builder:
    def __init__(
        self,
        working_directory_path: Path,
        entrypoint_providers: Sequence[WebpackEntrypointProvider & Extension],
        debug: bool,
        renderer: Renderer,
        *,
        job_context: Context,
        localizer: Localizer,
    ) -> None:
        self._working_directory_path = working_directory_path
        self._entrypoint_providers = entrypoint_providers
        self._debug = debug
        self._renderer = renderer
        self._job_context = job_context
        self._localizer = localizer

    async def _copy2_and_render(
        self, source_path: Path, destination_path: Path
    ) -> None:
        await makedirs(destination_path.parent, exist_ok=True)
        await to_thread(copy2, source_path, destination_path)
        await self._renderer.render_file(
            source_path,
            job_context=self._job_context,
            localizer=self._localizer,
        )

    async def _copytree_and_render(
        self, source_path: Path, destination_path: Path
    ) -> None:
        await gather(
            *[
                self._copy2_and_render(
                    file_source_path,
                    destination_path / file_source_path.relative_to(source_path),
                )
                async for file_source_path in iterfiles(source_path)
            ]
        )

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

    async def _prepare_webpack_entrypoint_provider(
        self,
        npm_project_directory_path: Path,
        entrypoint_provider: type[WebpackEntrypointProvider & Extension],
        npm_project_package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
    ) -> None:
        entrypoint_provider_working_directory_path = (
            npm_project_directory_path / "entrypoints" / entrypoint_provider.name()
        )
        await self._copytree_and_render(
            entrypoint_provider.webpack_entrypoint_directory_path(),
            entrypoint_provider_working_directory_path,
        )
        npm_project_package_json_dependencies[entrypoint_provider.name()] = (
            # Ensure a relative path inside the npm project directory, or else npm
            # will not install our entrypoints' dependencies.
            f"file:{entrypoint_provider_working_directory_path.relative_to(npm_project_directory_path)}"
        )
        # Webpack requires relative paths to start with a leading dot and use forward slashes.
        webpack_entry[entrypoint_provider.name()] = "/".join(
            (
                ".",
                *(entrypoint_provider_working_directory_path / "main.ts")
                .relative_to(npm_project_directory_path)
                .parts,
            )
        )

    async def _prepare_npm_project_directory(
        self, npm_project_directory_path: Path, webpack_build_directory_path: Path
    ) -> None:
        npm_project_package_json_dependencies: MutableMapping[str, str] = {}
        webpack_entry: MutableMapping[str, str] = {}
        await makedirs(npm_project_directory_path, exist_ok=True)
        await gather(
            self._prepare_webpack_extension(npm_project_directory_path),
            *(
                self._prepare_webpack_entrypoint_provider(
                    npm_project_directory_path,
                    type(entrypoint_provider),
                    npm_project_package_json_dependencies,
                    webpack_entry,
                )
                for entrypoint_provider in self._entrypoint_providers
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

    async def _npm_install(self, npm_project_directory_path: Path) -> None:
        await _npm.npm(("install", "--production"), cwd=npm_project_directory_path)

    async def _webpack_build(
        self, npm_project_directory_path: Path, webpack_build_directory_path: Path
    ) -> None:
        await _npm.npm(("run", "webpack"), cwd=npm_project_directory_path)

        # Ensure there is always a vendor.css. This makes for easy and unconditional importing.
        await makedirs(webpack_build_directory_path / "css", exist_ok=True)
        await to_thread((webpack_build_directory_path / "css" / "vendor.css").touch)

    async def build(self) -> Path:
        npm_project_directory_path = await _npm_project_directory_path(
            self._working_directory_path, self._entrypoint_providers, self._debug
        )
        webpack_build_directory_path = _webpack_build_directory_path(
            npm_project_directory_path,
            self._entrypoint_providers,
        )
        if webpack_build_directory_path.exists():
            return webpack_build_directory_path
        npm_install_required = not npm_project_directory_path.exists()
        await self._prepare_npm_project_directory(
            npm_project_directory_path, webpack_build_directory_path
        )
        if npm_install_required:
            await self._npm_install(npm_project_directory_path)
        await self._webpack_build(
            npm_project_directory_path, webpack_build_directory_path
        )
        getLogger(__name__).info(
            self._localizer._("Built the Webpack front-end assets.")
        )
        return webpack_build_directory_path
