from __future__ import annotations

import logging
import os
import shutil
import sys
from asyncio import subprocess as aiosubprocess
from contextlib import suppress
from pathlib import Path
from subprocess import CalledProcessError
from typing import Sequence, Set, Optional, Type

from aiofiles.tempfile import TemporaryDirectory

from betty import subprocess
from betty.app.extension import Extension, discover_extension_types
from betty.asyncio import sync
from betty.requirement import Requirement, AnyRequirement


async def npm(arguments: Sequence[str], **kwargs) -> aiosubprocess.Process:
    # Use a shell on Windows so subprocess can find the executables it needs (see
    # https://bugs.python.org/issue17023).
    runner = subprocess.run_shell if sys.platform.startswith('win32') else subprocess.run_exec
    return await runner(['npm', *arguments], **kwargs)


class _NpmRequirement(Requirement):
    def __init__(self, met: bool):
        self._met = met
        self._summary = self._met_summary() if met else self._unmet_summary()
        self._details = _('npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`.')

    @classmethod
    def _met_summary(cls) -> str:
        return _('`npm` is available')

    @classmethod
    def _unmet_summary(cls) -> str:
        return _('`npm` is not available')

    @classmethod
    @sync
    async def check(cls) -> _NpmRequirement:
        try:
            await npm(['--version'])
            logging.getLogger().debug(cls._met_summary())
            return cls(True)
        except (CalledProcessError, FileNotFoundError):
            logging.getLogger().debug(cls._unmet_summary())
            return cls(False)

    @property
    def met(self) -> bool:
        return self._met

    @property
    def summary(self) -> str:
        return self._summary

    @property
    def details(self) -> Optional[str]:
        return self._details


class _AssetsRequirement(Requirement):
    def __init__(self, extension_types: Set[Type[Extension | NpmBuilder]]):
        self._extension_types = extension_types
        self._summary = _('Pre-built assets')
        if not self.met:
            extension_names = sorted(
                extension_type.name()
                for extension_type
                in self._extension_types - self._extension_types_with_built_assets
            )
            self._details = _('Pre-built assets are unavailable for {extension_names}.').format(extension_names=', '.join(extension_names))
        else:
            self._details = None

    @property
    def _extension_types_with_built_assets(self) -> Set[Type[Extension | NpmBuilder]]:
        return {
            extension_type
            for extension_type
            in self._extension_types
            if _get_assets_build_directory_path(extension_type).is_dir()
        }

    @property
    def met(self) -> bool:
        return self._extension_types <= self._extension_types_with_built_assets

    @property
    def summary(self) -> str:
        return self._summary

    @property
    def details(self) -> Optional[str]:
        return self._details


class NpmBuilder:
    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        raise NotImplementedError


def discover_npm_builders() -> Set[Type[Extension | NpmBuilder]]:
    return {
        extension_type
        for extension_type
        in discover_extension_types()
        if issubclass(extension_type, NpmBuilder)
    }


def _get_assets_directory_path(extension_type: Type[Extension | NpmBuilder]) -> Path:
    return extension_type.assets_directory_path() / _Npm.name()


def _get_assets_src_directory_path(extension_type: Type[Extension | NpmBuilder]) -> Path:
    return _get_assets_directory_path(extension_type) / 'src'


def _get_assets_build_directory_path(extension_type: Type[Extension | NpmBuilder]) -> Path:
    return _get_assets_directory_path(extension_type) / 'build'


async def build_assets(extension: Extension | NpmBuilder) -> Path:
    assets_directory_path = _get_assets_build_directory_path(type(extension))
    await _build_assets_to_directory_path(extension, assets_directory_path)
    return assets_directory_path


async def _build_assets_to_directory_path(extension: Extension | NpmBuilder, assets_directory_path: Path) -> None:
    with suppress(FileNotFoundError):
        shutil.rmtree(assets_directory_path)
    os.makedirs(assets_directory_path)
    async with TemporaryDirectory() as working_directory_path:
        await extension.npm_build(Path(working_directory_path), assets_directory_path)


class _Npm(Extension):
    _npm_requirement = None
    _assets_requirement = None
    _requirement = None

    @classmethod
    def _ensure_requirements(cls) -> None:
        if cls._requirement is None:
            cls._npm_requirement = _NpmRequirement.check()
            cls._assets_requirement = _AssetsRequirement(discover_npm_builders())
            cls._requirement = AnyRequirement([cls._npm_requirement, cls._assets_requirement])

    @classmethod
    def requires(cls) -> Requirement:
        cls._ensure_requirements()
        return super().requires() + cls._requirement

    async def install(self, extension_type: Type[Extension | NpmBuilder], working_directory_path: Path) -> None:
        self._ensure_requirements()
        self._npm_requirement.assert_met()

        shutil.copytree(
            _get_assets_src_directory_path(extension_type),
            working_directory_path,
            dirs_exist_ok=True,
        )
        await self._app.renderer.render_tree(working_directory_path)
        await npm(['install', '--production'], cwd=working_directory_path)

    def _get_cached_assets_build_directory_path(self, extension_type: Type[Extension | NpmBuilder]) -> Path:
        return self._app.configuration.cache_directory_path / self.name() / extension_type.name()

    async def ensure_assets(self, extension: Extension | NpmBuilder) -> Path:
        assets_build_directory_paths = [
            _get_assets_build_directory_path(type(extension)),
            self._get_cached_assets_build_directory_path(type(extension)),
        ]
        for assets_build_directory_path in assets_build_directory_paths:
            if assets_build_directory_path.is_dir():
                return assets_build_directory_path

        self._npm_requirement.assert_met()
        return await self._build_cached_assets(extension)

    async def _build_cached_assets(self, extension: Extension | NpmBuilder) -> Path:
        assets_directory_path = self._get_cached_assets_build_directory_path(type(extension))
        await _build_assets_to_directory_path(extension, assets_directory_path)
        return assets_directory_path
