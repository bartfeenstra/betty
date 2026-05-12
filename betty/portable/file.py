"""
Configuration file management.
"""

from __future__ import annotations

from asyncio import to_thread
from contextlib import chdir
from typing import TYPE_CHECKING

from betty.assertion import AssertionChain, assert_file
from betty.exception import reraise_with_indicator
from betty.file import write
from betty.indicator import Path as IndicatorPath
from betty.pathlib import resolve_path
from betty.serde import Serializer, serializer_for

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from betty.pathlib import StrPath
    from betty.portable import PortableData


def assert_load_file(
    *, serializers: Iterable[Serializer]
) -> AssertionChain[StrPath, PortableData]:
    """
    An assertion to load a dump from a file.
    """

    def _assert(file: Path, /) -> PortableData:
        file = resolve_path(file)
        with (
            reraise_with_indicator(IndicatorPath(file)),
            # Change the working directory to allow relative paths to be resolved
            # against the configuration file's directory path.
            chdir(file.parent),
        ):
            with open(file, encoding="utf-8") as f:
                dump_data = f.read()
            return serializer_for(serializers, file.suffix).load(dump_data)

    return assert_file() | _assert


async def dump_file(
    portable: PortableData, file: StrPath, *, serializers: Iterable[Serializer]
) -> None:
    """
    Write a dump to a file.
    """
    file = resolve_path(file)
    dump_data = serializer_for(serializers, file.suffix).dump(portable)
    await to_thread(file.parent.mkdir, exist_ok=True, parents=True)
    await write(file, dump_data)
