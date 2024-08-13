"""
Test utilities for :py:mod:`betty.ancestry`.
"""

from typing_extensions import override

from betty.ancestry import Dated, HasPrivacy, Described, HasLocale
from betty.json.linked_data import LinkedDataDumpable
from betty.json.schema import Object
from betty.project import Project


class _LinkedDataObjectSchema(LinkedDataDumpable[Object]):
    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> Object:
        return Object()


class DummyDated(Dated, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.Dated` implementation.
    """

    pass


class DummyDescribed(Described, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.Described` implementation.
    """

    pass


class DummyHasLocale(HasLocale, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.HasLocale` implementation.
    """

    pass


class DummyHasPrivacy(HasPrivacy, _LinkedDataObjectSchema):
    """
    A dummy :py:class:`betty.ancestry.HasPrivacy` implementation.
    """

    pass
