"""
Test utilities for :py:mod:`betty.json.linked_data`.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, MutableMapping, MutableSequence
from typing import TYPE_CHECKING

from betty.app import App
from betty.json.schema import Schema
from betty.portable import PortableData
from betty.project import Project

if TYPE_CHECKING:
    from betty.json.linked_data import (
        LinkedDataDumpableWithSchema,
        LinkedDataDumper,
    )


async def assert_dumps_linked_data[PortableDataT: PortableData](
    sut: LinkedDataDumpableWithSchema[Schema, PortableDataT],
) -> PortableDataT:
    """
    Dump an object's linked data and assert it is valid.
    """
    return await assert_linked_data_dump(sut.linked_data_schema, sut.dump_linked_data)


async def assert_dumps_linked_data_for[PortableDataT: PortableData, T](
    sut: LinkedDataDumper[T, Schema, PortableDataT], target: T
) -> PortableDataT:
    """
    Dump an object's linked data and assert it is valid.
    """

    async def _dump(project: Project) -> PortableDataT:
        return await sut.dump_linked_data_for(project, target)

    return await assert_linked_data_dump(sut.linked_data_schema_for, _dump)


async def assert_linked_data_dump[PortableDataT: PortableData](
    schema: Callable[[Project], Awaitable[Schema]] | Schema,
    portable: Callable[[Project], Awaitable[PortableDataT]] | PortableDataT,
) -> PortableDataT:
    """
    Assert that dumped linked data is valid against a schema.
    """
    async with (
        App.new_isolated() as app,
        app,
        Project.new_isolated(app) as project,
        project,
    ):
        actual = await portable(project) if callable(portable) else portable  # ty:ignore[call-top-callable]

        # Validate the raw dump.
        sut_schema = schema if isinstance(schema, Schema) else await schema(project)
        sut_schema.validate(actual)

        # Normalize the dump after validation (so we are assured it is absolutely valid),
        # but before returning, so calling code can use simpler comparisons.
        return _normalize(actual)


def _normalize[PortableDataT: PortableData](portable: PortableDataT) -> PortableDataT:
    if isinstance(portable, MutableMapping):
        return {
            key: _normalize(value)
            for key, value in portable.items()
            if not key.startswith("$")
        }  # ty:ignore[invalid-return-type]
    if isinstance(portable, MutableSequence) and not isinstance(portable, str):
        return list(
            map(
                _normalize,
                portable,  # ty:ignore[invalid-argument-type]
            )
        )  # ty:ignore[invalid-return-type]
    return portable
