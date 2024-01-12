"""
Integrate Betty with Webpack.
"""
from __future__ import annotations

from asyncio import to_thread
from collections.abc import Callable, Sequence
from hashlib import md5
from json import dumps, loads
from logging import getLogger
from pathlib import Path
from shutil import copytree
from typing import Any

import aiofiles

from betty.app.extension import Extension
from betty.asyncio import gather
from betty.extension.npm import _Npm, npm
from betty.extension.webpack.jinja2.filter import FILTERS
from betty.fs import iterfiles
from betty.generate import Generator, GenerationContext
from betty.html import CssProvider
from betty.jinja2 import Jinja2Provider


class _WebpackEntrypointProvider:
    @classmethod
    def webpack_entrypoint_directory_path(cls) -> Path:
        raise NotImplementedError


async def build_package_assets(extensions: Sequence[type[_WebpackEntrypointProvider & Extension]]) -> Path:
    """
    Build the Webpack assets for a Betty package build.
    """
    # @todo We should probable create a new root build/package/dist directory for these assets.
    # @todo
    # @todo
    # assets_directory_path = _get_assets_build_directory_path(type(extension))
    # await _build_assets_to_directory_path(extension, assets_directory_path)
    # return assets_directory_path
    return Path()


async def _build_assets_to_directory_path(extensions: Sequence[type[_WebpackEntrypointProvider & Extension]], assets_directory_path: Path) -> None:
    # @todo
    pass
    # with suppress(FileNotFoundError):
    #     await to_thread(rmtree, assets_directory_path)
    # await makedirs(assets_directory_path)
    # async with TemporaryDirectory() as working_directory_path_str:
    #     working_directory_path = Path(
    #         working_directory_path_str,  # type: ignore[arg-type]
    #     )
    #     await extension.npm_build(Path(working_directory_path), assets_directory_path)


class _Webpack(Extension, CssProvider, Jinja2Provider, Generator):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_Npm}

    @classmethod
    def assets_directory_path(cls) -> Path:
        return Path(__file__).parent / 'assets'

    @property
    def public_css_paths(self) -> list[str]:
        return [
            self.app.static_url_generator.generate('css/vendor.css'),
        ]

    def new_context_vars(self) -> dict[str, Any]:
        return {
            'webpack_js_entrypoints': set(),
        }

    @property
    def filters(self) -> dict[str, Callable[..., Any]]:
        return FILTERS

    async def generate(self, job_context: GenerationContext) -> None:
        entrypoint_providers: Sequence[_WebpackEntrypointProvider & Extension] = [
            extension
            for extension
            in self._app.extensions.flatten()
            if isinstance(extension, _WebpackEntrypointProvider)
        ]
        build_id_extensions = md5(':'.join(
            extension.name()
            for extension
            in entrypoint_providers
        ).encode()).hexdigest()
        build_id_debug = 'true' if self._app.project.configuration.debug else 'false'
        build_id = f'{build_id_extensions}-{build_id_debug}'
        working_directory_path = self._app.binary_file_cache.with_scope('webpack').with_scope(build_id).path

        # @todo Check for cached builds here.
        # @todo
        # @todo Do this after we've fixed integration tests, because they fail when we don't mock caches
        # @todo (or until we add this check here, but we should use these failures to mock caches...)
        # @todo

        build_directory_path = await self._generate_to_working_directory(
            entrypoint_providers,
            working_directory_path,
            job_context,
        )

        # Copy build artifacts to the output directory.
        await to_thread(
            copytree,
            build_directory_path,
            self._app.project.configuration.www_directory_path,
            dirs_exist_ok=True,
        )

        getLogger(__name__).info(self._app.localizer._('Built the Webpack front-end assets.'))

    # @todo When caching, consider reintroducing scopes.
    # @todo We don't want to cache anything that depends on a project, for instance, or at least NOT FOR PACKAGE BUILDS
    # @todo
    # @todo
    async def _generate_to_working_directory(
        self,
        extensions: Sequence[_WebpackEntrypointProvider & Extension],
        working_directory_path: Path,
        job_context: GenerationContext,
    ) -> Path:
        # Prepare the working directory.
        await to_thread(
            copytree,
            Path(__file__).parent / 'webpack',
            working_directory_path,
        )
        entrypoints_working_directory_path = working_directory_path / 'entrypoints'
        working_package_json_dependencies = {}
        webpack_entry = {}
        for extension in extensions:
            extension_webpack_entrypoint_directory_path = extension.webpack_entrypoint_directory_path()
            extension_working_directory_path = entrypoints_working_directory_path / extension.name()
            await to_thread(
                copytree,
                extension_webpack_entrypoint_directory_path,
                extension_working_directory_path,
            )
            working_package_json_dependencies[extension.name()] = f'file:{extension_working_directory_path}'
            webpack_entry[extension.name()] = str((extension_working_directory_path / 'main.js').resolve())
        webpack_configuration_json = dumps({
            'debug': self._app.project.configuration.debug,
            'cacheDirectory': str(self._app.binary_file_cache.with_scope('webpack-babel').path),
            'entry': webpack_entry,
        })
        async with aiofiles.open(working_directory_path / 'webpack.config.json', 'w') as configuration_f:
            await configuration_f.write(webpack_configuration_json)
        await gather(*[
            self._app.renderer.render_file(
                file_path,
                job_context=job_context,
            )
            async for file_path
            in iterfiles(working_directory_path)
        ])

        # Add dependencies to package.json.
        working_package_json_path = working_directory_path / 'package.json'
        async with aiofiles.open(working_package_json_path, 'r') as working_package_json_f:
            working_package_json = loads(await working_package_json_f.read())
        working_package_json['dependencies'].update(working_package_json_dependencies)
        async with aiofiles.open(working_package_json_path, 'w') as working_package_json_f:
            await working_package_json_f.write(dumps(working_package_json))

        # Install third-party dependencies.
        install_arguments = ['install']
        if not self._app.project.configuration.debug:
            install_arguments.append('--production')
        await npm(install_arguments, cwd=working_directory_path)

        # Run Webpack.
        await npm(('run', 'webpack'), cwd=working_directory_path)

        build_directory_path = working_directory_path / 'build'

        # Ensure there is always a vendor.css
        await to_thread((build_directory_path / 'css' / 'vendor.css').touch)

        return build_directory_path
