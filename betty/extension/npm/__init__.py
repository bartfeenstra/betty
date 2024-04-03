"""
Provide tools to integrate extensions with `npm <https://www.npmjs.com/>`_.

This extension and module are internal.
"""
from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sys
from asyncio import subprocess as aiosubprocess
from contextlib import suppress
from enum import unique, IntFlag, auto
from pathlib import Path
from subprocess import CalledProcessError
from typing import Sequence

from aiofiles.tempfile import TemporaryDirectory

from betty.app.extension import Extension, discover_extension_types
from betty.app.extension.requirement import Requirement, AnyRequirement, AllRequirements
from betty.asyncio import wait
from betty.cache.file import BinaryFileCache
from betty.fs import iterfiles
from betty.locale import Str, DEFAULT_LOCALIZER
from betty.subprocess import run_process


async def npm(
    arguments: Sequence[str],
    cwd: Path | None = None,
) -> aiosubprocess.Process:
    """
    Run an npm command.
    """
    return await run_process(
        ['npm', *arguments],
        cwd=cwd,
        # Use a shell on Windows so subprocess can find the executables it needs (see
        # https://bugs.python.org/issue17023).
        shell=sys.platform.startswith('win32'),
    )


class _NpmRequirement(Requirement):
    def __init__(self, met: bool):
        super().__init__()
        self._met = met
        self._summary = self._met_summary() if met else self._unmet_summary()
        self._details = Str._('npm (https://www.npmjs.com/) must be available for features that require Node.js packages to be installed. Ensure that the `npm` executable is available in your `PATH`.')

    @classmethod
    def _met_summary(cls) -> Str:
        return Str._('`npm` is available')

    @classmethod
    def _unmet_summary(cls) -> Str:
        return Str._('`npm` is not available')

    @classmethod
    def check(cls) -> _NpmRequirement:
        try:
            wait(npm(['--version']))
            logging.getLogger(__name__).debug(cls._met_summary().localize(DEFAULT_LOCALIZER))
            return cls(True)
        except (CalledProcessError, FileNotFoundError):
            logging.getLogger(__name__).debug(cls._unmet_summary().localize(DEFAULT_LOCALIZER))
            return cls(False)

    def is_met(self) -> bool:
        return self._met

    def summary(self) -> Str:
        return self._summary

    def details(self) -> Str:
        return self._details


def is_assets_build_directory_path(path: Path) -> bool:
    """
    Check if the given path is an assets build directory path.
    """
    return path.is_dir() and len(os.listdir(path)) > 0


class _AssetsRequirement(Requirement):
    def __init__(self, extension_types: set[type[_NpmBuilder & Extension]]):
        super().__init__()
        self._extension_types = extension_types
        self._summary = Str._('Pre-built assets')
        self._details: Str
        if not self.is_met():
            extension_names = sorted(
                extension_type.name()
                for extension_type
                in self._extension_types - self._extension_types_with_built_assets
            )
            self._details = Str._(
                'Pre-built assets are unavailable for {extension_names}.',
                extension_names=', '.join(extension_names,
                                          ))
        else:
            self._details = Str.plain('')

    @property
    def _extension_types_with_built_assets(self) -> set[type[_NpmBuilder & Extension]]:
        return {
            extension_type
            for extension_type
            in self._extension_types
            if is_assets_build_directory_path(_get_assets_build_directory_path(extension_type))
        }

    def is_met(self) -> bool:
        return self._extension_types <= self._extension_types_with_built_assets

    def summary(self) -> Str:
        return self._summary

    def details(self) -> Str:
        return self._details


@unique
class _NpmBuilderCacheScope(IntFlag):
    BETTY = auto()
    PROJECT = auto()


class _NpmBuilder:
    async def npm_build(self, working_directory_path: Path, assets_directory_path: Path) -> None:
        raise NotImplementedError(repr(self))

    @classmethod
    def npm_cache_scope(cls) -> _NpmBuilderCacheScope:
        return _NpmBuilderCacheScope.PROJECT


def discover_npm_builders() -> set[type[_NpmBuilder & Extension]]:
    """
    Gather all extensions that are npm builders.
    """
    return {
        extension_type
        for extension_type
        in discover_extension_types()
        if issubclass(extension_type, _NpmBuilder)
    }


def _get_assets_directory_path(extension_type: type[_NpmBuilder & Extension]) -> Path:
    assert issubclass(extension_type, Extension)
    assert issubclass(extension_type, _NpmBuilder)
    assets_directory_path = extension_type.assets_directory_path()
    if not assets_directory_path:
        raise RuntimeError(f'Extension {extension_type} does not have an assets directory.')
    return assets_directory_path / _Npm.name()


def _get_assets_src_directory_path(extension_type: type[_NpmBuilder & Extension]) -> Path:
    return _get_assets_directory_path(extension_type) / 'src'


def _get_assets_build_directory_path(extension_type: type[_NpmBuilder & Extension]) -> Path:
    return _get_assets_directory_path(extension_type) / 'build'


async def build_assets(extension: _NpmBuilder & Extension) -> Path:
    """
    Build the npm assets for an extension.
    """
    assets_directory_path = _get_assets_build_directory_path(type(extension))
    await _build_assets_to_directory_path(extension, assets_directory_path)
    return assets_directory_path


async def _build_assets_to_directory_path(extension: _NpmBuilder & Extension, assets_directory_path: Path) -> None:
    assert isinstance(extension, Extension)
    assert isinstance(extension, _NpmBuilder)
    with suppress(FileNotFoundError):
        await asyncio.to_thread(shutil.rmtree, assets_directory_path)
    os.makedirs(assets_directory_path)
    async with TemporaryDirectory() as working_directory_path_str:
        working_directory_path = Path(working_directory_path_str)
        await extension.npm_build(Path(working_directory_path), assets_directory_path)


class _Npm(Extension):
    _npm_requirement: _NpmRequirement | None = None
    _assets_requirement: _AssetsRequirement | None = None
    _requirement: Requirement | None = None

    @classmethod
    def _ensure_requirement(cls) -> Requirement:
        if cls._requirement is None:
            cls._npm_requirement = _NpmRequirement.check()
            cls._assets_requirement = _AssetsRequirement(discover_npm_builders())
            assert cls._npm_requirement is not None
            assert cls._assets_requirement is not None
            cls._requirement = AnyRequirement(cls._npm_requirement, cls._assets_requirement)
        return cls._requirement

    @classmethod
    def enable_requirement(cls) -> Requirement:
        return AllRequirements(
            cls._ensure_requirement(),
            super().enable_requirement(),
        )

    async def install(self, extension_type: type[_NpmBuilder & Extension], working_directory_path: Path) -> None:
        self._ensure_requirement()
        if self._npm_requirement:
            self._npm_requirement.assert_met()

        await asyncio.to_thread(
            shutil.copytree,
            _get_assets_src_directory_path(extension_type),
            working_directory_path,
            dirs_exist_ok=True,
        )
        async for file_path in iterfiles(working_directory_path):
            await self._app.renderer.render_file(file_path)
        await npm(['install', '--production'], cwd=working_directory_path)

    def _get_assets_build_cache(self, extension_type: type[_NpmBuilder & Extension]) -> BinaryFileCache:
        cache = self._app.binary_file_cache.with_scope(self.name()).with_scope(extension_type.name())
        if extension_type.npm_cache_scope() == _NpmBuilderCacheScope.PROJECT:
            cache = cache.with_scope(self.app.project.name)
        return cache

    async def ensure_assets(self, extension: _NpmBuilder & Extension) -> Path:
        assets_build_directory_paths = [
            _get_assets_build_directory_path(type(extension)),
            self._get_assets_build_cache(type(extension)).path,
        ]
        for assets_build_directory_path in assets_build_directory_paths:
            if is_assets_build_directory_path(assets_build_directory_path):
                return assets_build_directory_path

        if self._npm_requirement:
            self._npm_requirement.assert_met()
        return (await self._build_cached_assets(extension)).path

    async def _build_cached_assets(self, extension: _NpmBuilder & Extension) -> BinaryFileCache:
        cache = self._get_assets_build_cache(type(extension))
        await _build_assets_to_directory_path(extension, cache.path)
        return cache
