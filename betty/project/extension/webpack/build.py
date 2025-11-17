"""
Perform Webpack builds.
"""

from __future__ import annotations

import json
from abc import abstractmethod
from asyncio import gather, to_thread
from collections.abc import Mapping, Sequence
from json import dumps, loads
from os import walk
from pathlib import Path
from shutil import copy2, copytree
from typing import TYPE_CHECKING, cast

import aiofiles
from aiofiles.os import makedirs

from betty import _npm
from betty.dirs import ROOT_DIRECTORY_PATH
from betty.hashid import hashid, hashid_file_content, hashid_sequence
from betty.project.extension import Extension
from betty.render import make_copy_function
from betty.resource import new_context
from betty.serde.dump import Dump, DumpMapping

if TYPE_CHECKING:
    from collections.abc import MutableMapping, Sequence

    from betty.job import Context
    from betty.render import Renderer
    from betty.user import User

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

    @abstractmethod
    def webpack_entry_point_cache_keys(self) -> Sequence[str]:
        """
        Get the keys that make a Webpack build for this provider unique.

        Providers that can be cached regardless may ``return ()``.
        """


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


def _package_name_to_path(package_name: str) -> Path:
    return Path(*package_name.split("/"))


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
        root_path: str,
        *,
        job_context: Context,
        user: User,
    ) -> None:
        self._working_directory_path = working_directory_path
        self._entry_point_providers = entry_point_providers
        self._debug = debug
        self._renderer = renderer
        self._root_path = root_path
        self._job_context = job_context
        self._user = user

    async def _prepare_betty(self, npm_project_directory_path: Path) -> None:
        await to_thread(
            copytree,
            ROOT_DIRECTORY_PATH / "js",
            npm_project_directory_path
            / "packages"
            / _package_name_to_path("@betty.py/betty"),
            dirs_exist_ok=True,
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

    async def _prepare_webpack_entry_point_provider(
        self,
        npm_project_directory_path: Path,
        package_json: DumpMapping[Dump],
        entry_point_provider: type[EntryPointProvider & Extension],
        npm_project_package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
    ) -> None:
        entry_point_directory_path = (
            entry_point_provider.webpack_entry_point_directory_path()
        )
        entry_point_provider_working_directory_path = (
            npm_project_directory_path
            / "packages"
            / _package_name_to_path(cast(str, package_json["name"]))
        )
        copy_function = make_copy_function(
            self._renderer,
            resource=new_context(job_context=self._job_context),
        )
        copies = []
        for directory_path, _, file_names in walk(entry_point_directory_path):
            for file_name in file_names:
                relative_file_path = (
                    Path(directory_path).relative_to(entry_point_directory_path)
                    / file_name
                )
                copies.append(
                    copy_function(
                        entry_point_directory_path / relative_file_path,
                        entry_point_provider_working_directory_path
                        / relative_file_path,
                    )
                )
        await gather(*copies)
        npm_project_package_json_dependencies[entry_point_provider.plugin.id] = (
            # Ensure a relative path inside the npm project directory, or else npm
            # will not install our entry points' dependencies.
            f"file:{entry_point_provider_working_directory_path.relative_to(npm_project_directory_path)}"
        )
        # Webpack requires relative paths to start with a leading dot and use forward slashes.
        webpack_entry[entry_point_provider.plugin.id] = "/".join(
            (
                ".",
                *(entry_point_provider_working_directory_path / "main.ts")
                .relative_to(npm_project_directory_path)
                .parts,
            )
        )

    async def _extract_package_json(self, package_path: Path) -> DumpMapping[Dump]:
        async with aiofiles.open(package_path / "package.json") as f:
            package_json_data = await f.read()
        return cast(DumpMapping[Dump], json.loads(package_json_data))

    async def _update_package_json(
        self,
        npm_project_directory_path: Path,
        package_jsons_by_package_name: MutableMapping[str, DumpMapping[Dump]],
        package_name: str,
    ) -> None:
        package_json = package_jsons_by_package_name[package_name]
        try:
            dependencies = package_json["dependencies"]
            assert isinstance(dependencies, Mapping)
        except KeyError:
            return
        for dependency_package_name in dependencies:
            if dependency_package_name not in package_jsons_by_package_name:
                continue
            # Manually compute the relative path to the dependency's package directory, because
            # pathlib.Path.relative_to()'s walk_up argument is only available in Python 3.12 and newer.
            dependency_package_path = Path(
                *(
                    [".."]
                    * len(
                        (
                            npm_project_directory_path
                            / "packages"
                            / _package_name_to_path(package_name)
                        )
                        .relative_to(npm_project_directory_path)
                        .parts
                    )
                ),
                *(
                    npm_project_directory_path
                    / "packages"
                    / _package_name_to_path(dependency_package_name)
                )
                .relative_to(npm_project_directory_path)
                .parts,
            )
            dependencies[dependency_package_name] = f"file:{dependency_package_path}"
        package_json_data = json.dumps(package_json)
        async with aiofiles.open(
            npm_project_directory_path / "packages" / package_name / "package.json", "w"
        ) as f:
            await f.write(package_json_data)

    async def _update_package_jsons(
        self,
        npm_project_directory_path: Path,
        package_jsons_by_package_name: MutableMapping[str, DumpMapping[Dump]],
    ) -> None:
        await gather(
            *(
                self._update_package_json(
                    npm_project_directory_path,
                    package_jsons_by_package_name,
                    package_name,
                )
                for package_name in package_jsons_by_package_name
            )
        )

    async def _prepare_npm_project_directory(
        self, npm_project_directory_path: Path, webpack_build_directory_path: Path
    ) -> None:
        package_paths = [
            ROOT_DIRECTORY_PATH / "js",
            *(
                entry_point_provider.webpack_entry_point_directory_path()
                for entry_point_provider in self._entry_point_providers
            ),
        ]
        package_jsons_by_package_path: MutableMapping[Path, DumpMapping[Dump]] = dict(
            zip(
                package_paths,
                await gather(
                    *(
                        self._extract_package_json(package_path)
                        for package_path in package_paths
                    )
                ),
                strict=True,
            )
        )
        package_jsons_by_package_name: MutableMapping[str, DumpMapping[Dump]] = {
            cast(str, package_json["name"]): package_json
            for package_json in package_jsons_by_package_path.values()
        }

        npm_project_package_json_dependencies: MutableMapping[str, str] = {}
        webpack_entry: MutableMapping[str, str] = {}
        await makedirs(npm_project_directory_path, exist_ok=True)
        await gather(
            self._prepare_betty(npm_project_directory_path),
            self._prepare_webpack_extension(npm_project_directory_path),
            *(
                self._prepare_webpack_entry_point_provider(
                    npm_project_directory_path,
                    package_jsons_by_package_path[
                        entry_point_provider.webpack_entry_point_directory_path()
                    ],
                    type(entry_point_provider),
                    npm_project_package_json_dependencies,
                    webpack_entry,
                )
                for entry_point_provider in self._entry_point_providers
            ),
        )
        await self._update_package_jsons(
            npm_project_directory_path, package_jsons_by_package_name
        )
        webpack_configuration_json = dumps(
            {
                "rootPath": self._root_path,
                # Use a relative path so we avoid portability issues with
                # leading root slashes or drive letters.
                "buildDirectoryPath": str(
                    webpack_build_directory_path.relative_to(npm_project_directory_path)
                ),
                "debug": self._debug,
                "entry": webpack_entry,
                "jobContextId": self._job_context.id,
            }
        )
        async with aiofiles.open(
            npm_project_directory_path / "webpack.config.json", "w"
        ) as configuration_f:
            await configuration_f.write(webpack_configuration_json)

        # Add dependencies to package.json.
        npm_project_package_json_path = npm_project_directory_path / "package.json"
        async with aiofiles.open(
            npm_project_package_json_path
        ) as npm_project_package_json_f:
            npm_project_package_json = loads(await npm_project_package_json_f.read())
        npm_project_package_json["dependencies"].update(  # type: ignore[call-overload,index,union-attr]
            npm_project_package_json_dependencies
        )
        async with aiofiles.open(
            npm_project_package_json_path, "w"
        ) as npm_project_package_json_f:
            await npm_project_package_json_f.write(dumps(npm_project_package_json))

    async def _npm_install(self, npm_project_directory_path: Path) -> None:
        await _npm.npm(
            ("install", "--production"), cwd=npm_project_directory_path, user=self._user
        )

    async def _webpack_build(
        self, npm_project_directory_path: Path, webpack_build_directory_path: Path
    ) -> None:
        await _npm.npm(
            ("run", "webpack"), cwd=npm_project_directory_path, user=self._user
        )

        # Ensure there is always a webpack-vendor.css. This makes for easy and unconditional importing.
        await makedirs(webpack_build_directory_path / "css" / "webpack", exist_ok=True)
        await to_thread(
            (
                webpack_build_directory_path / "css" / "webpack" / "webpack-vendor.css"
            ).touch
        )

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
        return webpack_build_directory_path
