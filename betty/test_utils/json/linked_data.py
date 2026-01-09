"""
Test utilities for :py:mod:`betty.json.linked_data`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import TYPE_CHECKING

from typing_extensions import TypeVar

from betty.app import App
from betty.json.schema import Schema
from betty.portable import PortableData
from betty.project import Project

if TYPE_CHECKING:
    from betty.json.linked_data import (
        LinkedDataDumpableProvider,
        LinkedDataDumpableWithSchema,
    )

_T = TypeVar("_T")
_PortableDataT = TypeVar("_PortableDataT", bound=PortableData, default=PortableData)


async def assert_dumps_linked_data(
    sut: LinkedDataDumpableWithSchema[Schema, _PortableDataT],
) -> _PortableDataT:
    """
    Dump an object's linked data and assert it is valid.
    """
    return await assert_linked_data_dump(sut.linked_data_schema, sut.dump_linked_data)  # ty:ignore[invalid-return-type]


async def assert_dumps_linked_data_for(
    sut: LinkedDataDumpableProvider[_T, Schema, _PortableDataT], target: _T
) -> _PortableDataT:
    """
    Dump an object's linked data and assert it is valid.
    """

    async def _dump(project: Project) -> _PortableDataT:
        return await sut.dump_linked_data_for(project, target)

    return await assert_linked_data_dump(sut.linked_data_schema_for, _dump)  # ty:ignore[invalid-return-type]


async def assert_linked_data_dump(
    schema: Callable[[Project], Awaitable[Schema]] | Schema,
    portable: Callable[[Project], Awaitable[_PortableDataT]] | _PortableDataT,
) -> _PortableDataT:
    """
    Assert that dumped linked data is valid against a schema.
    """
    async with (
        App.new_isolated() as app,
        app,
        Project.new_isolated(app) as project,
        project,
    ):
        actual = await portable(project) if callable(portable) else portable

        # Validate the raw dump.
        sut_schema = schema if isinstance(schema, Schema) else await schema(project)
        sut_schema.validate(actual)

        # Normalize the dump after validation (so we are assured it is absolutely valid),
        # but before returning, so calling code can use simpler comparisons.
        return _normalize(actual)


def _normalize(portable: _PortableDataT) -> _PortableDataT:
    if isinstance(portable, Mapping):
        return {
            key: _normalize(value)
            for key, value in portable.items()
            if not key.startswith("$")
        }  # ty:ignore[invalid-return-type]
    if isinstance(portable, Sequence) and not isinstance(portable, str):
        return list(
            map(
                _normalize,
                portable,  # ty:ignore[invalid-argument-type]
            )
        )  # ty:ignore[invalid-return-type]
    return portable
