"""
Configuration file management.
"""

from __future__ import annotations

from contextlib import chdir
from typing import TYPE_CHECKING

import aiofiles
from aiofiles.os import makedirs

from betty.assertion import AssertionChain, assert_file_path
from betty.data import Path as DataPath
from betty.exception import reraise_within_context
from betty.factory import new_target
from betty.plugin.repository.provider.service import plugins
from betty.serde.format import FormatDefinition, format_for

if TYPE_CHECKING:
    from pathlib import Path

    from betty.serde.dump import Dump


async def assert_load_file() -> AssertionChain[Path, Dump]:
    """
    An assertion to load a dump from a file.
    """
    available_formats = {
        available_format: await new_target(available_format.cls)
        for available_format in await plugins(FormatDefinition)
    }

    def _assert(file_path: Path) -> Dump:
        with (
            reraise_within_context(DataPath(file_path)),
            # Change the working directory to allow relative paths to be resolved
            # against the configuration file's directory path.
            chdir(file_path.parent),
        ):
            with open(file_path) as f:
                dump_data = f.read()
            file_format = available_formats[
                format_for(list(available_formats), file_path.suffix)
            ]
            return file_format.load(dump_data)

    return assert_file_path() | _assert


async def dump_file(dump: Dump, file_path: Path, /) -> None:
    """
    Write a dump to a file.
    """
    serde_format_type = format_for(
        list(await plugins(FormatDefinition)), file_path.suffix
    )
    serde_format = await new_target(serde_format_type.cls)
    dump_data = serde_format.dump(dump)
    await makedirs(file_path.parent, exist_ok=True)
    async with aiofiles.open(file_path, mode="w") as f:
        await f.write(dump_data)
