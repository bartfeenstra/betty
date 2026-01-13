"""
Test utilities for :py:mod:`betty.json.linked_data`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import TYPE_CHECKING

from typing_extensions import TypeVar

from betty.app import App
from betty.json.schema import Schema
from betty.project import Project
from betty.serde import SerializedData

if TYPE_CHECKING:
    from betty.json.linked_data import (
        LinkedDataDumpableProvider,
        LinkedDataDumpableWithSchema,
    )

_T = TypeVar("_T")
_SerializedDataT = TypeVar(
    "_SerializedDataT", bound=SerializedData, default=SerializedData
)


async def assert_dumps_linked_data(
    sut: LinkedDataDumpableWithSchema[Schema, _SerializedDataT],
) -> _SerializedDataT:
    """
    Dump an object's linked data and assert it is valid.
    """
    return await assert_linked_data_dump(sut.linked_data_schema, sut.dump_linked_data)


async def assert_dumps_linked_data_for(
    sut: LinkedDataDumpableProvider[_T, Schema, _SerializedDataT], target: _T
) -> _SerializedDataT:
    """
    Dump an object's linked data and assert it is valid.
    """

    async def _dump(project: Project) -> _SerializedDataT:
        return await sut.dump_linked_data_for(project, target)

    return await assert_linked_data_dump(sut.linked_data_schema_for, _dump)


async def assert_linked_data_dump(
    schema: Callable[[Project], Awaitable[Schema]] | Schema,
    serialized: Callable[[Project], Awaitable[_SerializedDataT]] | _SerializedDataT,
) -> _SerializedDataT:
    """
    Assert that dumped linked data is valid against a schema.
    """
    async with (
        App.new_isolated() as app,
        app,
        Project.new_isolated(app) as project,
        project,
    ):
        actual = await serialized(project) if callable(serialized) else serialized

        # Validate the raw dump.
        sut_schema = schema if isinstance(schema, Schema) else await schema(project)
        sut_schema.validate(actual)

        # Normalize the dump after validation (so we are assured it is absolutely valid),
        # but before returning, so calling code can use simpler comparisons.
        return _normalize(actual)


def _normalize(serialized: _SerializedDataT) -> _SerializedDataT:
    if isinstance(serialized, Mapping):
        return {  # type: ignore[return-value]
            key: _normalize(value)
            for key, value in serialized.items()
            if not key.startswith("$")
        }
    if isinstance(serialized, Sequence) and not isinstance(serialized, str):
        return list(map(_normalize, serialized))  # type: ignore[return-value]
    return serialized  # type: ignore[return-value]
