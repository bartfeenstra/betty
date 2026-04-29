from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, override

import pytest

from betty.cache.file import BinaryFileCache, PickledFileCache
from betty.test_utils.cache import CacheTestBase


class TestPickledFileCache(CacheTestBase[Any]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AsyncIterator[PickledFileCache[Any]]:
        with TemporaryDirectory() as cache_directory:
            yield PickledFileCache(cache_directory, scopes=scopes)

    @override
    def _values(self) -> Iterator[Any]:
        yield True
        yield None
        yield 123
        yield 123.456
        yield []
        yield {}


class TestBinaryFileCache(CacheTestBase[bytes]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AsyncIterator[BinaryFileCache]:
        with TemporaryDirectory() as cache_directory:
            yield BinaryFileCache(cache_directory, scopes=scopes)

    @override
    def _values(self) -> Iterator[bytes]:
        yield b"SomeBytes"

    @pytest.mark.parametrize(
        "scopes",
        [
            (),
            ("scopey", "dopey"),
        ],
    )
    def test_directory(self, scopes: Sequence[str], tmp_path: Path) -> None:
        sut = BinaryFileCache(tmp_path, scopes=scopes)
        assert sut.directory == tmp_path.joinpath(*scopes)

    @pytest.mark.parametrize(
        ("expected_path_components", "scopes"),
        [
            (("b80bb7740288fda1f201890375a60c8f",), ()),
            (
                (
                    "scopey",
                    "dopey",
                    "b80bb7740288fda1f201890375a60c8f",
                ),
                (
                    "scopey",
                    "dopey",
                ),
            ),
        ],
    )
    def test_cache_item_file(
        self,
        expected_path_components: Sequence[str],
        scopes: Sequence[str],
        tmp_path: Path,
    ) -> None:
        sut = BinaryFileCache(tmp_path, scopes=scopes)
        assert sut.cache_item_file("id") == tmp_path.joinpath(*expected_path_components)
