"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableSequence
from inspect import getmembers
from typing import TYPE_CHECKING, cast, override

from betty.json_schema import Object, Schema
from betty.json_schemas.json_ld import JsonLdSchema
from betty.portable import PortableData, PortableMapping
from betty.string import snake_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.entities.link import Link
    from betty.locale.localizable import ResolvableLocalizable
    from betty.project import Project


async def dump_schema(
    project: Project,
    portable: PortableMapping,
    linked_data_dumpable: LinkedDataDumpableWithSchema[Object, PortableMapping],
    /,
) -> None:
    """
    Add the $schema item to a JSON-LD dump.
    """
    from betty.json_schemas.project import ProjectSchema

    schema = await linked_data_dumpable.linked_data_schema(project)
    if schema.def_name:
        portable["$schema"] = await ProjectSchema.def_url(project, schema.def_name)


class LinkedDataDumpable[PortableDataT: PortableData = PortableData]:
    """
    Describe an object that can be dumped to linked data.
    """

    @abstractmethod
    async def dump_linked_data(self, project: Project, /) -> PortableDataT:
        """
        Dump this instance to `JSON-LD <https://json-ld.org/>`_.
        """


class LinkedDataDumpableWithSchema[
    SchemaT: Schema,
    PortableDataT: PortableData = PortableData,
](LinkedDataDumpable[PortableDataT]):
    """
    Describe an object that can be dumped to linked data.
    """

    @classmethod
    @abstractmethod
    async def linked_data_schema(cls, project: Project, /) -> SchemaT:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.linked_data.LinkedDataDumpable.dump_linked_data`.
        """


class JsonLdObject(Object):
    """
    A JSON Schema for an object with JSON-LD.
    """

    def __init__(
        self,
        *,
        def_name: str | None = None,
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            def_name=def_name,
            title=title,
            description=description,
        )
        self.schema["allOf"] = [JsonLdSchema().embed(self)]


class LinkedDataDumpableWithSchemaJsonLdObject(
    LinkedDataDumpableWithSchema[JsonLdObject, PortableMapping], ABC
):
    """
    A :py:class:`betty.linked_data.LinkedDataDumpable` implementation for object/mapping data.

    This is helpful when working with diamond class hierarchies where parent classes that may not be the root class want
    to make changes to the linked data, and expect an :py:class`betty.json_schema.Object` schema and a
    :py:type:`betty.portable.PortableMapping` dump.
    """

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = JsonLdObject()
        for attr_name, class_attr_value in getmembers(cls):
            if isinstance(class_attr_value, LinkedDataDumper):
                linked_data_dumpable = class_attr_value
                schema.add_property(
                    snake_case_to_lower_camel_case(attr_name),
                    await linked_data_dumpable.linked_data_schema_for(project),
                    True,
                )
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        portable: PortableMapping = {}

        await dump_schema(project, portable, self)

        for attr_name, class_attr_value in getmembers(type(self)):
            if isinstance(class_attr_value, LinkedDataDumper):
                portable[
                    snake_case_to_lower_camel_case(attr_name)
                ] = await class_attr_value.dump_linked_data_for(project, self)

        return portable


class LinkedDataDumper[
    T,
    SchemaT: Schema = Schema,
    PortableDataT: PortableData = PortableData,
](ABC):
    """
    Provide linked data for instances of a target type.
    """

    @abstractmethod
    async def linked_data_schema_for(self, project: Project, /) -> SchemaT:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.linked_data.LinkedDataDumper.dump_linked_data_for`.
        """

    @abstractmethod
    async def dump_linked_data_for(
        self, project: Project, target: T, /
    ) -> PortableDataT:
        """
        Dump the given target to `JSON-LD <https://json-ld.org/>`_.
        """


def dump_context(portable: PortableMapping, **context_definitions: str) -> None:
    """
    Add one or more contexts to a dump.
    """
    portable_context = cast(PortableMapping, portable.setdefault("@context", {}))
    for key, context_definition in context_definitions.items():
        portable_context[key] = context_definition


async def dump_link(portable: PortableMapping, project: Project, *links: Link) -> None:
    """
    Add one or more links to a dump.
    """
    portable_link = cast(
        MutableSequence[PortableMapping],
        portable.setdefault("links", []),
    )
    for link in links:
        portable_link.append(await link.dump_linked_data(project))
