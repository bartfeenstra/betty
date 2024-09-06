"""
Test utilities for :py:mod:`betty.json.linked_data`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from betty.app import App
from betty.project import Project

if TYPE_CHECKING:
    from betty.json.schema import Schema
    from betty.json.linked_data import LinkedDataDumpable
    from betty.serde.dump import Dump


async def assert_dumps_linked_data(sut: LinkedDataDumpable[Schema]) -> Dump:
    """
    Dump an object's linked data and assert it is valid.
    """
    async with (
        App.new_temporary() as app,
        app,
        Project.new_temporary(app) as project,
        project,
    ):
        actual = await sut.dump_linked_data(project)

        # Validate the raw dump.
        sut_schema = await sut.linked_data_schema(project)
        sut_schema.validate(actual)

        # Normalize the dump after validation (so we are assured it is absolutely valid),
        # but before returning, so calling code can use simpler comparisons.
        return _normalize(actual)


def _normalize(dump: Dump) -> Dump:
    if isinstance(dump, Mapping):
        return {
            key: _normalize(value)
            for key, value in dump.items()
            if not key.startswith("$")
        }
    if isinstance(dump, Sequence) and not isinstance(dump, str):
        return list(map(_normalize, dump))
    return dump
