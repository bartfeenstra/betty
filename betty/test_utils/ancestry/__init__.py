"""
Test utilities for :py:mod:`betty.ancestry`.
"""

from typing_extensions import override

from betty.ancestry import HasDate, HasDescription, HasLocale
from betty.json.linked_data import LinkedDataDumpable
from betty.json.schema import Object
from betty.project import Project


class _LinkedDataObjectSchema(LinkedDataDumpable[Object]):
    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        return Object()


class DummyHasDate(HasDate, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.HasDate` implementation.
    """

    pass


class DummyHasDescription(HasDescription, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.HasDescription` implementation.
    """

    pass


class DummyHasLocale(HasLocale, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.HasLocale` implementation.
    """

    pass
