"""
Test utilities for :py:mod:`betty.json.linked_data`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import TYPE_CHECKING

from typing_extensions import TypeVar

from betty.app import App
from betty.project import Project
from betty.serde.dump import Dump

if TYPE_CHECKING:
    from betty.json.linked_data import (
        LinkedDataDumpableProvider,
        LinkedDataDumpableWithSchema,
    )
    from betty.json.schema import Schema

_T = TypeVar("_T")
_DumpT = TypeVar("_DumpT", bound=Dump, default=Dump)


async def assert_dumps_linked_data(
    sut: LinkedDataDumpableWithSchema[Schema, _DumpT],
) -> _DumpT:
    """
    Dump an object's linked data and assert it is valid.
    """
    return await _assert_linked_data_dump(sut.linked_data_schema, sut.dump_linked_data)


async def assert_dumps_linked_data_for(
    sut: LinkedDataDumpableProvider[_T, Schema, _DumpT], target: _T
) -> _DumpT:
    """
    Dump an object's linked data and assert it is valid.
    """

    async def _dump(project: Project) -> _DumpT:
        return await sut.dump_linked_data_for(project, target)

    return await _assert_linked_data_dump(sut.linked_data_schema_for, _dump)


async def _assert_linked_data_dump(
    schema: Callable[[Project], Awaitable[Schema]],
    dump: Callable[[Project], Awaitable[_DumpT]],
) -> _DumpT:
    async with (
        App.new_temporary() as app,
        app,
        Project.new_temporary(app) as project,
        project,
    ):
        actual = await dump(project)

        # Validate the raw dump.
        sut_schema = await schema(project)
        sut_schema.validate(actual)

        # Normalize the dump after validation (so we are assured it is absolutely valid),
        # but before returning, so calling code can use simpler comparisons.
        return _normalize(actual)


def _normalize(dump: _DumpT) -> _DumpT:
    if isinstance(dump, Mapping):
        return {  # type: ignore[return-value]
            key: _normalize(value)
            for key, value in dump.items()
            if not key.startswith("$")
        }
    if isinstance(dump, Sequence) and not isinstance(dump, str):
        return list(map(_normalize, dump))  # type: ignore[return-value]
    return dump  # type: ignore[return-value]
