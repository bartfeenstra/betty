"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableSequence
from inspect import getmembers
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Self, cast, final

from typing_extensions import TypeVar, override

from betty.json.schema import FileBasedSchema, Object, Schema
from betty.serde.dump import Dump, DumpMapping
from betty.string import snake_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.ancestry.link import Link
    from betty.project import Project


_T = TypeVar("_T")
_SchemaTypeT = TypeVar("_SchemaTypeT", bound=Schema, default=Schema, covariant=True)
_DumpT = TypeVar("_DumpT", bound=Dump, default=Dump)


async def dump_schema(
    project: Project,
    dump: DumpMapping[Dump],
    linked_data_dumpable: LinkedDataDumpable[Object, DumpMapping[Dump]],
) -> None:
    """
    Add the $schema item to a JSON-LD dump.
    """
    from betty.project import ProjectSchema

    schema = await linked_data_dumpable.linked_data_schema(project)
    if schema.def_name:
        dump["$schema"] = await ProjectSchema.def_url(project, schema.def_name)


class LinkedDataDumpable(Generic[_SchemaTypeT, _DumpT]):
    """
    Describe an object that can be dumped to linked data.
    """

    @classmethod
    @abstractmethod
    async def linked_data_schema(cls, project: Project) -> _SchemaTypeT:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.json.linked_data.LinkedDataDumpable.dump_linked_data`.
        """

    @abstractmethod
    async def dump_linked_data(self, project: Project) -> _DumpT:
        """
        Dump this instance to `JSON-LD <https://json-ld.org/>`_.
        """


class JsonLdObject(Object):
    """
    A JSON Schema for an object with JSON-LD.
    """

    def __init__(
        self,
        json_ld_schema: JsonLdSchema,
        *,
        def_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        super().__init__(
            def_name=def_name,
            title=title,
            description=description,
        )
        self._schema["allOf"] = [json_ld_schema.embed(self)]


class LinkedDataDumpableJsonLdObject(
    LinkedDataDumpable[JsonLdObject, DumpMapping[Dump]], ABC
):
    """
    A :py:class:`betty.json.linked_data.LinkedDataDumpable` implementation for object/mapping data.

    This is helpful when working with diamond class hierarchies where parent classes that may not be the root class want
    to make changes to the linked data, and expect an :py:class`betty.json.schema.Object` schema and a
    :py:type:`betty.serde.dump.DumpMapping` dump.
    """

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = JsonLdObject(await JsonLdSchema.new())
        for attr_name, class_attr_value in getmembers(cls):
            if isinstance(class_attr_value, LinkedDataDumpableProvider):
                linked_data_dumpable = class_attr_value
                schema.add_property(
                    snake_case_to_lower_camel_case(attr_name),
                    await linked_data_dumpable.linked_data_schema_for(project),
                    True,
                )
        return schema

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump: DumpMapping[Dump] = {}

        await dump_schema(project, dump, self)

        for attr_name, class_attr_value in getmembers(type(self)):
            if isinstance(class_attr_value, LinkedDataDumpableProvider):
                dump[
                    snake_case_to_lower_camel_case(attr_name)
                ] = await class_attr_value.dump_linked_data_for(project, self)

        return dump


class LinkedDataDumpableProvider(Generic[_T, _SchemaTypeT, _DumpT], ABC):
    """
    Provide linked data for instances of a target type.
    """

    @abstractmethod
    async def linked_data_schema_for(self, project: Project) -> _SchemaTypeT:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.json.linked_data.LinkedDataDumpableProvider.dump_linked_data_for`.
        """

    @abstractmethod
    async def dump_linked_data_for(self, project: Project, target: _T) -> _DumpT:
        """
        Dump the given target to `JSON-LD <https://json-ld.org/>`_.
        """


def dump_context(dump: DumpMapping[Dump], **context_definitions: str) -> None:
    """
    Add one or more contexts to a dump.
    """
    context_dump = cast(DumpMapping[Dump], dump.setdefault("@context", {}))
    for key, context_definition in context_definitions.items():
        context_dump[key] = context_definition


async def dump_link(dump: DumpMapping[Dump], project: Project, *links: Link) -> None:
    """
    Add one or more links to a dump.
    """
    link_dump = cast(MutableSequence[DumpMapping[Dump]], dump.setdefault("links", []))
    for link in links:
        link_dump.append(await link.dump_linked_data(project))


@final
class JsonLdSchema(FileBasedSchema):
    """
    A `JSON-LD <https://json-ld.org/>`_ JSON Schema reference.
    """

    _instance: Self | None = None

    @classmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """
        if cls._instance is None:
            cls._instance = await cls.new_for(
                Path(__file__).parent / "schemas" / "json-ld.json",
                def_name="jsonLd",
                title="JSON-LD",
            )
        return cls._instance
