"""
Test utilities for :py:mod:`betty.json.linked_data`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from betty.app import App
from betty.json.schema import ProjectSchema
from betty.project import Project, LocaleConfiguration

if TYPE_CHECKING:
    from betty.json.linked_data import LinkedDataDumpable
    from betty.serde.dump import Dump


async def assert_dumps_linked_data(dumpable: LinkedDataDumpable) -> Dump:
    """
    Dump an object's linked data and assert it is valid.
    """
    async with App.new_temporary() as app, app, Project.new_temporary(app) as project:
        project.configuration.locales["en-US"].alias = "en"
        project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        async with project:
            project_schema = await ProjectSchema.new(project)
            dumpable_schema = await dumpable.linked_data_schema(project)
            dumpable_schema.embed(project_schema)
            actual = await dumpable.dump_linked_data(project)
            if "$id" not in actual:
                actual["$id"] = project.static_url_generator.generate(
                    "schema.json", absolute=True
                )
            project_schema.validate(actual)

            # Normalize the data after validation (so we are assured it is absolutely valid),
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
