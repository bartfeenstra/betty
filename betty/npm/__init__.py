from __future__ import annotations

import hashlib
import logging
import os
import shutil
import sys
from asyncio import subprocess as aiosubprocess
from contextlib import suppress
from pathlib import Path
from subprocess import CalledProcessError
from typing import Sequence, Set, Optional, Type

from betty import subprocess
from betty.app.extension import Extension, discover_extension_types
from betty.app.extension.requirement import Requirement, AnyRequirement, AllRequirements
from betty.asyncio import sync
from betty.cache import CacheScope
from betty.fs import iterfiles
from betty.locale import Localizer, DEFAULT_LOCALIZER
from betty.tempfile import TemporaryDirectory


async def npm(arguments: Sequence[str], **kwargs) -> aiosubprocess.Process:
    # Use a shell on Windows so subprocess can find the executables it needs (see
    # https://bugs.python.org/issue17023).
    runner = subprocess.run_shell if sys.platform.startswith('win32') else subprocess.run_exec
    return await runner(['npm', *arguments], **kwargs)


class _NpmRequirement(Requirement):
    def __init__(self, met: bool, *, localizer: Localizer | None):
        super().__init__(localizer=localizer)
        self._met = met
        self._summary = self._met_summary(self.localizer) if met else self._unmet_summary(self.localizer)
        self._details = self.localizer._('npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`.')

    @classmethod
    def _met_summary(cls, localizer: Localizer) -> str:
        return localizer._('`npm` is available')

    @classmethod
    def _unmet_summary(cls, localizer: Localizer) -> str:
        return localizer._('`npm` is not available')

    @classmethod
    @sync
    async def check(cls, localizer: Localizer) -> _NpmRequirement:
        try:
            await npm(['--version'])
            logging.getLogger().debug(cls._met_summary(localizer))
            return cls(True, localizer=localizer)
        except (CalledProcessError, FileNotFoundError):
            logging.getLogger().debug(cls._unmet_summary(localizer=localizer))
            return cls(False, localizer=localizer)

    def is_met(self) -> bool:
        return self._met

    def summary(self) -> str:
        return self._summary

    def details(self) -> Optional[str]:
        return self._details


def is_assets_build_directory_path(path: Path) -> bool:
    return path.is_dir() and len(os.listdir(path)) > 0


class _AssetsRequirement(Requirement):
    def __init__(self, extension_types: Set[Type[Extension] | Type[NpmBuilder]], *, localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._extension_types = extension_types
        self._summary = self.localizer._('Pre-built assets')
        self._details: Optional[str]
        if not self.is_met():
            extension_names = sorted(
                extension_type.name()  # type: ignore
                for extension_type
                in self._extension_types - self._extension_types_with_built_assets
            )
            self._details = self.localizer._('Pre-built assets are unavailable for {extension_names}.').format(extension_names=', '.join(extension_names))
        else:
            self._details = None

    @property
    def _extension_types_with_built_assets(self) -> Set[Type[Extension | NpmBuilder]]:
        return {
            extension_type
            for extension_type
            in self._extension_types
            if is_assets_build_directory_path(_get_assets_build_directory_path(extension_type))
        }

    def is_met(self) -> bool:
        return self._extension_types <= self._extension_types_with_built_assets

    def summary(self) -> str:
        return self._summary

    def details(self) -> Optional[str]:
        return self._details


class NpmBuilder:
    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        raise NotImplementedError(repr(self))

    @classmethod
    def npm_cache_scope(cls) -> CacheScope:
        return CacheScope.PROJECT


def discover_npm_builders() -> Set[Type[Extension | NpmBuilder]]:
    return {
        extension_type
        for extension_type
        in discover_extension_types()
        if issubclass(extension_type, NpmBuilder)
    }


def _get_assets_directory_path(extension_type: Type[Extension | NpmBuilder]) -> Path:
    assert issubclass(extension_type, Extension)
    assert issubclass(extension_type, NpmBuilder)
    assets_directory_path = extension_type.assets_directory_path()
    if not assets_directory_path:
        raise RuntimeError(f'Extension {extension_type} does not have an assets directory.')
    return assets_directory_path / _Npm.name()


def _get_assets_src_directory_path(extension_type: Type[Extension | NpmBuilder]) -> Path:
    return _get_assets_directory_path(extension_type) / 'src'


def _get_assets_build_directory_path(extension_type: Type[Extension | NpmBuilder]) -> Path:
    return _get_assets_directory_path(extension_type) / 'build'


async def build_assets(extension: Extension | NpmBuilder) -> Path:
    assets_directory_path = _get_assets_build_directory_path(type(extension))
    await _build_assets_to_directory_path(extension, assets_directory_path)
    return assets_directory_path


async def _build_assets_to_directory_path(extension: Extension | NpmBuilder, assets_directory_path: Path) -> None:
    assert isinstance(extension, Extension)
    assert isinstance(extension, NpmBuilder)
    with suppress(FileNotFoundError):
        shutil.rmtree(assets_directory_path)
    os.makedirs(assets_directory_path)
    with TemporaryDirectory() as working_directory_path:
        await extension.npm_build(working_directory_path, assets_directory_path)


class _Npm(Extension):
    _npm_requirement: Optional[_NpmRequirement] = None
    _assets_requirement: Optional[_AssetsRequirement] = None
    _requirement: Optional[Requirement] = None

    @classmethod
    def _ensure_requirement(cls, localizer: Localizer) -> Requirement:
        if cls._requirement is None:
            cls._npm_requirement = _NpmRequirement.check(localizer)
            cls._assets_requirement = _AssetsRequirement(discover_npm_builders())
            assert cls._npm_requirement is not None
            assert cls._assets_requirement is not None
            cls._requirement = AnyRequirement(cls._npm_requirement, cls._assets_requirement)
        return cls._requirement

    @classmethod
    def enable_requirement(cls, localizer: Localizer | None = None) -> Requirement:
        return AllRequirements(
            cls._ensure_requirement(DEFAULT_LOCALIZER),
            super().enable_requirement(localizer),
        )

    async def install(self, extension_type: Type[Extension | NpmBuilder], working_directory_path: Path) -> None:
        self._ensure_requirement(self._app.localizer)
        if self._npm_requirement:
            self._npm_requirement.assert_met()

        shutil.copytree(
            _get_assets_src_directory_path(extension_type),
            working_directory_path,
            dirs_exist_ok=True,
        )
        async for file_path in iterfiles(working_directory_path):
            await self._app.renderer.render_file(file_path)
        await npm(['install', '--production'], cwd=working_directory_path)

    def _get_cached_assets_build_directory_path(self, extension_type: Type[Extension | NpmBuilder]) -> Path:
        assert issubclass(extension_type, Extension) and issubclass(extension_type, NpmBuilder)
        path = self.cache_directory_path / extension_type.name()
        if extension_type.npm_cache_scope() == CacheScope.PROJECT:
            path /= hashlib.md5(str(self.app.project.configuration.configuration_file_path).encode('utf-8')).hexdigest()
        return path

    async def ensure_assets(self, extension: Extension | NpmBuilder) -> Path:
        assets_build_directory_paths = [
            _get_assets_build_directory_path(type(extension)),
            self._get_cached_assets_build_directory_path(type(extension)),
        ]
        for assets_build_directory_path in assets_build_directory_paths:
            if is_assets_build_directory_path(assets_build_directory_path):
                return assets_build_directory_path

        if self._npm_requirement:
            self._npm_requirement.assert_met()
        return await self._build_cached_assets(extension)

    async def _build_cached_assets(self, extension: Extension | NpmBuilder) -> Path:
        assets_directory_path = self._get_cached_assets_build_directory_path(type(extension))
        await _build_assets_to_directory_path(extension, assets_directory_path)
        return assets_directory_path
