"""
Configuration file management.
"""

from __future__ import annotations

from contextlib import chdir
from typing import TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs

from betty.assertion import AssertionChain, assert_file_path
from betty.data.indicator import Path as DataPath
from betty.exception import reraise_with_indicator
from betty.serde import SerializerDefinition, serializer_for
from betty.universe import UNIVERSE

if TYPE_CHECKING:
    from pathlib import Path

    from betty.portable import PortableData


async def assert_load_file() -> AssertionChain[Path, PortableData]:
    """
    An assertion to load a dump from a file.
    """
    available_formats = {
        available_format: await UNIVERSE.factory.new(available_format.cls)
        async for available_format in UNIVERSE.plugins[SerializerDefinition]
    }

    def _assert(file_path: Path) -> PortableData:
        with (
            reraise_with_indicator(DataPath(file_path)),
            # Change the working directory to allow relative paths to be resolved
            # against the configuration file's directory path.
            chdir(file_path.parent),
        ):
            with open(file_path, encoding="utf-8") as f:
                dump_data = f.read()
            file_format = available_formats[
                serializer_for(list(available_formats), file_path.suffix)
            ]
            return file_format.load(dump_data)

    return assert_file_path() | _assert


async def dump_file(portable: PortableData, file_path: Path, /) -> None:
    """
    Write a dump to a file.
    """
    serializer = await UNIVERSE.factory.new(
        serializer_for(
            [plugin async for plugin in UNIVERSE.plugins[SerializerDefinition]],
            file_path.suffix,
        ).cls
    )
    dump_data = serializer.dump(portable)
    await makedirs(file_path.parent, exist_ok=True)
    async with aiofiles.open(file_path, mode="w") as f:
        await f.write(dump_data)
