"""
Perform Webpack builds.
"""

from __future__ import annotations

from abc import abstractmethod
from asyncio import gather, to_thread
from json import dumps, loads
from pathlib import Path
from shutil import copy2, copytree
from typing import TYPE_CHECKING, Final, cast

from betty import npm
from betty.dirs import (
    js_directory,
    root_directory,
    webpack_entry_point_directory,
)
from betty.document import Document
from betty.extension import Extension
from betty.file import read, write
from betty.hashid import hashid, hashid_file_content, hashid_sequence
from betty.jinja import make_copy_function
from betty.pathlib import resolve_path
from betty.portable import PortableMapping

if TYPE_CHECKING:
    from collections.abc import MutableMapping, Sequence

    from betty.jinja import Environment
    from betty.job import Context
    from betty.pathlib import StrPath
    from betty.user import User

_NPM_PROJECT_DIRECTORY: Final[Path] = webpack_entry_point_directory / "webpack"


class EntryPointProvider(Extension):
    """
    An extension that provides Webpack entry points.
    """

    @classmethod
    @abstractmethod
    def webpack_entry_point_directory(cls) -> StrPath:
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
    entry_point_providers: Sequence[EntryPointProvider],
) -> str:
    return hashid_sequence(
        await hashid_file_content(_NPM_PROJECT_DIRECTORY / "package.json"),
        *[
            await hashid_file_content(
                resolve_path(entry_point_provider.webpack_entry_point_directory())
                / "package.json"
            )
            for entry_point_provider in entry_point_providers
        ],
    )


async def _npm_project_directory(
    working_directory: Path, entry_point_providers: Sequence[EntryPointProvider]
) -> Path:
    return working_directory / await _npm_project_id(entry_point_providers)


def webpack_build_id(
    entry_point_providers: Sequence[EntryPointProvider], debug: bool
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


def _webpack_build_directory(
    npm_project_directory: Path,
    entry_point_providers: Sequence[EntryPointProvider],
    debug: bool,
) -> Path:
    return (
        npm_project_directory
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
        entry_point_providers: Sequence[EntryPointProvider],
        debug: bool,
        jinja: Environment,
        root: str,
        *,
        user: User,
    ) -> None:
        self._entry_point_providers = entry_point_providers
        self._debug = debug
        self._jinja = jinja
        self._root = root
        self._user = user

    async def _prepare_betty(self, npm_project_directory: Path) -> None:
        await to_thread(
            copytree,
            js_directory,
            npm_project_directory
            / "packages"
            / _package_name_to_path("@betty.py/betty"),
            dirs_exist_ok=True,
        )

    async def _prepare_webpack_extension(self, npm_project_directory: Path) -> None:
        await gather(*[
            to_thread(copy2, source_file, npm_project_directory)
            for source_file in (
                _NPM_PROJECT_DIRECTORY / "package.json",
                _NPM_PROJECT_DIRECTORY / "webpack.config.js",
                root_directory / ".browserslistrc",
                root_directory / "tsconfig.json",
            )
        ])  # ty:ignore[no-matching-overload]

    async def _prepare_webpack_entry_point_provider(
        self,
        context: Context,
        npm_project_directory: Path,
        package_json: PortableMapping,
        entry_point_provider: type[EntryPointProvider],
        npm_project_package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
    ) -> None:
        entry_point_directory = resolve_path(
            entry_point_provider.webpack_entry_point_directory()
        )
        entry_point_provider_working_directory = (
            npm_project_directory
            / "packages"
            / _package_name_to_path(cast(str, package_json["name"]))
        )
        copy_function = make_copy_function(
            self._jinja, document=Document(context=context)
        )
        copies = []
        for directory, _, file_names in entry_point_directory.walk():
            for file_name in file_names:
                relative_file = directory.relative_to(entry_point_directory) / file_name
                copies.append(
                    copy_function(
                        entry_point_directory / relative_file,
                        entry_point_provider_working_directory / relative_file,
                    )
                )
        await gather(*copies)
        npm_project_package_json_dependencies[entry_point_provider.plugin().id] = (
            # Ensure a relative path inside the npm project directory, or else npm
            # will not install our entry points' dependencies.
            f"file:{entry_point_provider_working_directory.relative_to(npm_project_directory)}"
        )
        # Webpack requires relative paths to start with a leading dot and use forward slashes.
        webpack_entry[entry_point_provider.plugin().id] = "/".join((
            ".",
            *(entry_point_provider_working_directory / "main.ts")
            .relative_to(npm_project_directory)
            .parts,
        ))

    async def _extract_package_json(self, package: Path) -> PortableMapping:
        return cast(PortableMapping, loads(await read(package / "package.json")))

    async def _update_package_json(
        self,
        npm_project_directory: Path,
        package_jsons_by_package_name: PortableMapping[PortableMapping],
        package_name: str,
    ) -> None:
        package_json = package_jsons_by_package_name[package_name]
        try:
            dependencies = package_json["dependencies"]
        except KeyError:
            return
        for dependency_package_name in dependencies:
            if dependency_package_name not in package_jsons_by_package_name:
                continue
            # Manually compute the relative path to the dependency's package directory, because
            # pathlib.Path.relative_to()'s walk_up argument is only available in Python 3.12 and newer.
            dependency_package = Path(
                *(
                    [".."]
                    * len(
                        (
                            npm_project_directory
                            / "packages"
                            / _package_name_to_path(package_name)
                        )
                        .relative_to(npm_project_directory)
                        .parts
                    )
                ),
                *(
                    npm_project_directory
                    / "packages"
                    / _package_name_to_path(dependency_package_name)
                )
                .relative_to(npm_project_directory)
                .parts,
            )
            dependencies[dependency_package_name] = f"file:{dependency_package}"
        await write(
            npm_project_directory / "packages" / package_name / "package.json",
            dumps(package_json),
        )

    async def _update_package_jsons(
        self,
        npm_project_directory: Path,
        package_jsons_by_package_name: MutableMapping[str, PortableMapping],
    ) -> None:
        await gather(
            *(
                self._update_package_json(
                    npm_project_directory,
                    package_jsons_by_package_name,
                    package_name,
                )
                for package_name in package_jsons_by_package_name
            )
        )

    async def _prepare_npm_project_directory(
        self,
        context: Context,
        npm_project_directory: Path,
        webpack_build_directory: Path,
    ) -> None:
        packages = [
            js_directory,
            *(
                resolve_path(entry_point_provider.webpack_entry_point_directory())
                for entry_point_provider in self._entry_point_providers
            ),
        ]
        package_jsons_by_package: MutableMapping[Path, PortableMapping] = dict(
            zip(
                packages,
                await gather(
                    *(self._extract_package_json(package) for package in packages)
                ),
                strict=True,
            )
        )
        package_jsons_by_package_name: MutableMapping[str, PortableMapping] = {
            cast(str, package_json["name"]): package_json
            for package_json in package_jsons_by_package.values()
        }

        npm_project_package_json_dependencies: MutableMapping[str, str] = {}
        webpack_entry: MutableMapping[str, str] = {}
        await to_thread(npm_project_directory.mkdir, exist_ok=True, parents=True)
        await gather(
            self._prepare_betty(npm_project_directory),
            self._prepare_webpack_extension(npm_project_directory),
            *(
                self._prepare_webpack_entry_point_provider(
                    context,
                    npm_project_directory,
                    package_jsons_by_package[
                        resolve_path(
                            entry_point_provider.webpack_entry_point_directory()
                        )
                    ],
                    type(entry_point_provider),
                    npm_project_package_json_dependencies,
                    webpack_entry,
                )
                for entry_point_provider in self._entry_point_providers
            ),
        )
        await self._update_package_jsons(
            npm_project_directory, package_jsons_by_package_name
        )
        webpack_configuration_json = {
            "rootPath": self._root,
            # Use a relative path so we avoid portability issues with
            # leading root slashes or drive letters.
            "buildDirectoryPath": str(
                webpack_build_directory.relative_to(npm_project_directory)
            ),
            "debug": self._debug,
            "entry": webpack_entry,
            "jobContextId": context.id,
        }
        await write(
            npm_project_directory / "webpack.config.json",
            dumps(webpack_configuration_json),
        )

        # Add dependencies to package.json.
        npm_project_package_json_file = npm_project_directory / "package.json"
        npm_project_package_json = loads(await read(npm_project_package_json_file))
        npm_project_package_json["dependencies"].update(
            npm_project_package_json_dependencies
        )
        await write(npm_project_package_json_file, dumps(npm_project_package_json))

    async def _npm_install(self, npm_project_directory: Path) -> None:
        await npm.npm(
            ("install", "--production"), cwd=npm_project_directory, user=self._user
        )

    async def _webpack_build(
        self, npm_project_directory: Path, webpack_build_directory: Path
    ) -> None:
        await npm.npm(("run", "webpack"), cwd=npm_project_directory, user=self._user)

        # Ensure there is always a main.css. This makes for easy and unconditional importing.
        await to_thread(
            (webpack_build_directory / "css" / "webpack").mkdir,
            exist_ok=True,
            parents=True,
        )
        await to_thread(
            (webpack_build_directory / "css" / "webpack" / "main.css").touch
        )

    async def build(self, working_directory: Path, *, context: Context) -> Path:
        """
        Build the Webpack assets.

        :return: The path to the directory from which the assets can be copied to their
            final destination.
        """
        npm_project_directory = await _npm_project_directory(
            working_directory, self._entry_point_providers
        )
        webpack_build_directory = _webpack_build_directory(
            npm_project_directory, self._entry_point_providers, self._debug
        )
        if webpack_build_directory.exists():
            return webpack_build_directory
        npm_install_required = not npm_project_directory.exists()
        await self._prepare_npm_project_directory(
            context, npm_project_directory, webpack_build_directory
        )
        if npm_install_required:
            await self._npm_install(npm_project_directory)
        await self._webpack_build(npm_project_directory, webpack_build_directory)
        return webpack_build_directory
