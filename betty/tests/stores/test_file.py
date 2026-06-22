from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, override

import pytest

from betty.stores.file import (
    BinaryFileStore,
    PickledFileStore,
    TransientBinaryFileStore,
    TransientPickledFileStore,
)
from betty.test_utils.store import StoreTestBase, TransientStoreTestBase


class _TestPickledFileStore(StoreTestBase[Any]):
    @override
    def _values(self) -> Iterator[Any]:
        yield True
        yield None
        yield 123
        yield 123.456
        yield []
        yield {}


class TestPickledFileStore(_TestPickledFileStore):
    @override
    @asynccontextmanager
    async def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AsyncIterator[PickledFileStore[Any]]:
        with TemporaryDirectory() as cache_directory:
            yield PickledFileStore(cache_directory, scopes=scopes)


class TestTransientPickledFileStore(_TestPickledFileStore, TransientStoreTestBase[Any]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AsyncIterator[TransientPickledFileStore[Any]]:
        with TemporaryDirectory() as cache_directory:
            yield TransientPickledFileStore(cache_directory, scopes=scopes)


class _TestBinaryFileStore(StoreTestBase[bytes]):
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
        sut = TransientBinaryFileStore(tmp_path, scopes=scopes)
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
    def test_file(
        self,
        expected_path_components: Sequence[str],
        scopes: Sequence[str],
        tmp_path: Path,
    ) -> None:
        sut = TransientBinaryFileStore(tmp_path, scopes=scopes)
        assert sut.file("id") == tmp_path.joinpath(*expected_path_components)


class TestBinaryFileStore(_TestBinaryFileStore):
    @override
    @asynccontextmanager
    async def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AsyncIterator[BinaryFileStore]:
        with TemporaryDirectory() as cache_directory:
            yield BinaryFileStore(cache_directory, scopes=scopes)


class TestTransientBinaryFileStore(_TestBinaryFileStore, TransientStoreTestBase[bytes]):
    @override
    @asynccontextmanager
    async def _new_sut(
        self, *, scopes: Sequence[str] = ()
    ) -> AsyncIterator[TransientBinaryFileStore]:
        with TemporaryDirectory() as cache_directory:
            yield TransientBinaryFileStore(cache_directory, scopes=scopes)
