"""
Configuration file management.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import chdir
from typing import TYPE_CHECKING

from betty.assertion import AssertionChain, assert_file_path
from betty.data.indicator import Path as DataPath
from betty.exception import reraise_with_indicator
from betty.file import write
from betty.serde import Serializer, serializer_for

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from betty.portable import PortableData


def assert_load_file(
    *, serializers: Iterable[Serializer]
) -> AssertionChain[Path, PortableData]:
    """
    An assertion to load a dump from a file.
    """

    def _assert(file_path: Path) -> PortableData:
        with (
            reraise_with_indicator(DataPath(file_path)),
            # Change the working directory to allow relative paths to be resolved
            # against the configuration file's directory path.
            chdir(file_path.parent),
        ):
            with open(file_path, encoding="utf-8") as f:
                dump_data = f.read()
            return serializer_for(serializers, file_path.suffix).load(dump_data)

    return assert_file_path() | _assert


async def dump_file(
    portable: PortableData, file_path: Path, *, serializers: Iterable[Serializer]
) -> None:
    """
    Write a dump to a file.
    """
    dump_data = serializer_for(serializers, file_path.suffix).dump(portable)
    await to_thread(file_path.parent.mkdir, exist_ok=True, parents=True)
    await write(file_path, dump_data)
