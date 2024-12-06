"""
Perform Webpack builds.
"""

from __future__ import annotations

from abc import abstractmethod
from asyncio import to_thread, gather
from json import dumps, loads
from logging import getLogger
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, Sequence

import aiofiles
from aiofiles.os import makedirs

from betty import _npm
from betty.fs import ROOT_DIRECTORY_PATH
from betty.hashid import hashid, hashid_sequence, hashid_file_content
from betty.os import copy_tree
from betty.project.extension import Extension

if TYPE_CHECKING:
    from betty.job import Context
    from betty.locale.localizer import Localizer
    from betty.render import Renderer
    from collections.abc import Sequence, MutableMapping

_NPM_PROJECT_DIRECTORIES_PATH = Path(__file__).parent / "webpack"


class EntryPointProvider(Extension):
    """
    An extension that provides Webpack entry points.
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
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        """
        Get the keys that make a Webpack build for this provider unique.

        Providers that can be cached regardless may ``return ()``.
        """
        pass


async def _npm_project_id(
    entry_point_providers: Sequence[EntryPointProvider & Extension],
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


async def _npm_project_directory_path(
    working_directory_path: Path,
    entry_point_providers: Sequence[EntryPointProvider & Extension],
) -> Path:
    return working_directory_path / await _npm_project_id(entry_point_providers)


def webpack_build_id(
    entry_point_providers: Sequence[EntryPointProvider & Extension], debug: bool
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


def _webpack_build_directory_path(
    npm_project_directory_path: Path,
    entry_point_providers: Sequence[EntryPointProvider & Extension],
    debug: bool,
) -> Path:
    return (
        npm_project_directory_path
        / f"build-{webpack_build_id(entry_point_providers, debug)}"
    )


class Builder:
    """
    Build Webpack assets.
    """

    def __init__(
        self,
        working_directory_path: Path,
        entry_point_providers: Sequence[EntryPointProvider & Extension],
        debug: bool,
        renderer: Renderer,
        *,
        job_context: Context,
        localizer: Localizer,
    ) -> None:
        self._working_directory_path = working_directory_path
        self._entry_point_providers = entry_point_providers
        self._debug = debug
        self._renderer = renderer
        self._job_context = job_context
        self._localizer = localizer

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

    async def _prepare_webpack_entry_point_provider(
        self,
        npm_project_directory_path: Path,
        entry_point_provider: type[EntryPointProvider & Extension],
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

    async def _prepare_npm_project_directory(
        self, npm_project_directory_path: Path, webpack_build_directory_path: Path
    ) -> None:
        npm_project_package_json_dependencies: MutableMapping[str, str] = {}
        webpack_entry: MutableMapping[str, str] = {}
        await makedirs(npm_project_directory_path, exist_ok=True)
        await gather(
            self._prepare_webpack_extension(npm_project_directory_path),
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
        """
        Build the Webpack assets.

        :return: The path to the directory from which the assets can be copied to their
            final destination.
        """
        npm_project_directory_path = await _npm_project_directory_path(
            self._working_directory_path, self._entry_point_providers
        )
        webpack_build_directory_path = _webpack_build_directory_path(
            npm_project_directory_path, self._entry_point_providers, self._debug
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
