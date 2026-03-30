"""
Perform Webpack builds.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import gather, to_thread
from json import dumps, loads
from os import walk
from pathlib import Path
from shutil import copy2, copytree
from typing import TYPE_CHECKING, cast, final, override

from betty import npm
from betty.dirs import ROOT_DIRECTORY
from betty.document import Document
from betty.file import read, write
from betty.hashid import hashid, hashid_file_content, hashid_sequence
from betty.jinja import make_copy_function
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer
from betty.portable import PortableMapping
from betty.service.plugin import ServicePluginDefinition

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping, Sequence

    from betty.jinja import Environment
    from betty.job import Context
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires
    from betty.user import User

_NPM_PROJECT_DIRECTORIES_PATH = Path(__file__).parent / "webpack"


class WebpackEntryPoint(ABC, Plugin["WebpackEntryPointDefinition"]):
    """
    Expose a Webpack entry point to Betty.
    """

    @abstractmethod
    async def cache_keys(self) -> Sequence[str]:
        """
        Get the keys that make a Webpack build for this provider unique.

        Providers that can be cached regardless may ``return ()``.
        """


@final
@PluginTypeDefinition(
    "webpack-entry-point",
    label=_("Webpack entry point"),
    label_plural=_("Webpack entry points"),
    label_countable=ngettext(
        "{count} Webpack entry point", "{count} Webpack entry points"
    ),
)
class WebpackEntryPointDefinition(ServicePluginDefinition[WebpackEntryPoint]):
    """
    .. plugin_type:: webpack-entry-point.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        entry_point: Path,
        auto: bool = False,
        requires: Requires = (),
    ):
        super().__init__(plugin_id, auto=auto, requires=requires)
        self._entry_point = entry_point

    @property
    def entry_point(self) -> Path:
        """
        The path on disk to the entry point's directory.
        """
        return self._entry_point


@final
class WebpackEntryPointManufacturer(
    PluginManufacturer[WebpackEntryPointDefinition, WebpackEntryPoint]
):
    """
    The Webpack entry point manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[WebpackEntryPointDefinition]:
        return WebpackEntryPointDefinition


async def _npm_project_id(
    entry_point_providers: Iterable[WebpackEntryPoint],
) -> str:
    return hashid_sequence(
        await hashid_file_content(_NPM_PROJECT_DIRECTORIES_PATH / "package.json"),
        *[
            await hashid_file_content(
                entry_point_provider.plugin().entry_point / "package.json"
            )
            for entry_point_provider in entry_point_providers
        ],
    )


async def _npm_project_directory_path(
    working_directory_path: Path, entry_point_providers: Iterable[WebpackEntryPoint]
) -> Path:
    return working_directory_path / await _npm_project_id(entry_point_providers)


async def webpack_build_id(
    entry_point_providers: Iterable[WebpackEntryPoint], debug: bool
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
                    await entry_point_provider.cache_keys(),
                )
            )
            for entry_point_provider in entry_point_providers
        ),
    )


def _webpack_build_directory_path(
    npm_project_directory_path: Path,
    entry_point_providers: Iterable[WebpackEntryPoint],
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
        entry_point_providers: Iterable[WebpackEntryPoint],
        debug: bool,
        jinja: Environment,
        root_path: str,
        *,
        user: User,
    ) -> None:
        self._entry_point_providers = entry_point_providers
        self._debug = debug
        self._jinja = jinja
        self._root_path = root_path
        self._user = user

    async def _prepare_betty(self, npm_project_directory_path: Path) -> None:
        await to_thread(
            copytree,
            ROOT_DIRECTORY / "js",
            npm_project_directory_path
            / "packages"
            / _package_name_to_path("@betty.py/betty"),
            dirs_exist_ok=True,
        )

    async def _prepare_webpack_extension(
        self, npm_project_directory_path: Path
    ) -> None:
        await gather(*[
            to_thread(copy2, source_file_path, npm_project_directory_path)
            for source_file_path in (
                _NPM_PROJECT_DIRECTORIES_PATH / "package.json",
                _NPM_PROJECT_DIRECTORIES_PATH / "webpack.config.js",
                ROOT_DIRECTORY / ".browserslistrc",
                ROOT_DIRECTORY / "tsconfig.json",
            )
        ])

    async def _prepare_webpack_entry_point_provider(
        self,
        context: Context,
        npm_project_directory_path: Path,
        package_json: PortableMapping,
        entry_point_provider: type[WebpackEntryPoint],
        npm_project_package_json_dependencies: MutableMapping[str, str],
        webpack_entry: MutableMapping[str, str],
    ) -> None:
        entry_point_directory_path = entry_point_provider.plugin().entry_point
        entry_point_provider_working_directory_path = (
            npm_project_directory_path
            / "packages"
            / _package_name_to_path(cast(str, package_json["name"]))
        )
        copy_function = make_copy_function(
            self._jinja, document=Document(context=context)
        )
        copies = []
        for directory_path, __, file_names in walk(entry_point_directory_path):
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
        npm_project_package_json_dependencies[entry_point_provider.plugin().id] = (
            # Ensure a relative path inside the npm project directory, or else npm
            # will not install our entry points' dependencies.
            f"file:{entry_point_provider_working_directory_path.relative_to(npm_project_directory_path)}"
        )
        # Webpack requires relative paths to start with a leading dot and use forward slashes.
        webpack_entry[entry_point_provider.plugin().id] = "/".join((
            ".",
            *(entry_point_provider_working_directory_path / "main.ts")
            .relative_to(npm_project_directory_path)
            .parts,
        ))

    async def _extract_package_json(self, package_path: Path) -> PortableMapping:
        return cast(PortableMapping, loads(await read(package_path / "package.json")))

    async def _update_package_json(
        self,
        npm_project_directory_path: Path,
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
        await write(
            npm_project_directory_path / "packages" / package_name / "package.json",
            dumps(package_json),
        )

    async def _update_package_jsons(
        self,
        npm_project_directory_path: Path,
        package_jsons_by_package_name: MutableMapping[str, PortableMapping],
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
        self,
        context: Context,
        npm_project_directory_path: Path,
        webpack_build_directory_path: Path,
    ) -> None:
        package_paths = [
            ROOT_DIRECTORY / "js",
            *(
                entry_point_provider.plugin().entry_point
                for entry_point_provider in self._entry_point_providers
            ),
        ]
        package_jsons_by_package_path: MutableMapping[Path, PortableMapping] = dict(
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
        package_jsons_by_package_name: MutableMapping[str, PortableMapping] = {
            cast(str, package_json["name"]): package_json
            for package_json in package_jsons_by_package_path.values()
        }

        npm_project_package_json_dependencies: MutableMapping[str, str] = {}
        webpack_entry: MutableMapping[str, str] = {}
        await to_thread(npm_project_directory_path.mkdir, exist_ok=True, parents=True)
        await gather(
            self._prepare_betty(npm_project_directory_path),
            self._prepare_webpack_extension(npm_project_directory_path),
            *(
                self._prepare_webpack_entry_point_provider(
                    context,
                    npm_project_directory_path,
                    package_jsons_by_package_path[
                        entry_point_provider.plugin().entry_point
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
        webpack_configuration_json = {
            "rootPath": self._root_path,
            # Use a relative path so we avoid portability issues with
            # leading root slashes or drive letters.
            "buildDirectoryPath": str(
                webpack_build_directory_path.relative_to(npm_project_directory_path)
            ),
            "debug": self._debug,
            "entry": webpack_entry,
            "jobContextId": context.id,
        }
        await write(
            npm_project_directory_path / "webpack.config.json",
            dumps(webpack_configuration_json),
        )

        # Add dependencies to package.json.
        npm_project_package_json_path = npm_project_directory_path / "package.json"
        npm_project_package_json = loads(await read(npm_project_package_json_path))
        npm_project_package_json["dependencies"].update(
            npm_project_package_json_dependencies
        )
        await write(npm_project_package_json_path, dumps(npm_project_package_json))

    async def _npm_install(self, npm_project_directory_path: Path) -> None:
        await npm.npm(
            ("install", "--production"), cwd=npm_project_directory_path, user=self._user
        )

    async def _webpack_build(
        self, npm_project_directory_path: Path, webpack_build_directory_path: Path
    ) -> None:
        await npm.npm(
            ("run", "webpack"), cwd=npm_project_directory_path, user=self._user
        )

        # Ensure there is always a main.css. This makes for easy and unconditional importing.
        await to_thread(
            (webpack_build_directory_path / "css" / "webpack").mkdir,
            exist_ok=True,
            parents=True,
        )
        await to_thread(
            (webpack_build_directory_path / "css" / "webpack" / "main.css").touch
        )

    async def build(self, working_directory: Path, *, context: Context) -> Path:
        """
        Build the Webpack assets.

        :return: The path to the directory from which the assets can be copied to their
            final destination.
        """
        npm_project_directory_path = await _npm_project_directory_path(
            working_directory, self._entry_point_providers
        )
        webpack_build_directory_path = _webpack_build_directory_path(
            npm_project_directory_path, self._entry_point_providers, self._debug
        )
        if webpack_build_directory_path.exists():
            return webpack_build_directory_path
        npm_install_required = not npm_project_directory_path.exists()
        await self._prepare_npm_project_directory(
            context, npm_project_directory_path, webpack_build_directory_path
        )
        if npm_install_required:
            await self._npm_install(npm_project_directory_path)
        await self._webpack_build(
            npm_project_directory_path, webpack_build_directory_path
        )
        return webpack_build_directory_path
