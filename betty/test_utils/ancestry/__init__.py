"""
Test utilities for :py:mod:`betty.ancestry`.
"""

from typing_extensions import override

from betty.json.linked_data import LinkedDataDumpable
from betty.json.schema import Object
from betty.project import Project


class _LinkedDataObjectSchema(LinkedDataDumpable[Object]):
    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        return Object()
