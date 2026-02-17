"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import MutableSequence
from inspect import getmembers
from typing import TYPE_CHECKING, Generic, cast, final, override

from typing_extensions import TypeVar

from betty.classtools import Singleton
from betty.json.schema import Object, Schema
from betty.portable import PortableData, PortableMapping
from betty.string import snake_case_to_lower_camel_case

if TYPE_CHECKING:
    from betty.ancestry.link import Link
    from betty.locale.localizable import ResolvableLocalizable
    from betty.project import Project


_T = TypeVar("_T")
_SchemaTypeT = TypeVar("_SchemaTypeT", bound=Schema, default=Schema, covariant=True)
_PortableDataT = TypeVar("_PortableDataT", bound=PortableData, default=PortableData)


async def dump_schema(
    project: Project,
    portable: PortableMapping,
    linked_data_dumpable: LinkedDataDumpableWithSchema[Object, PortableMapping],
    /,
) -> None:
    """
    Add the $schema item to a JSON-LD dump.
    """
    from betty.project.schema import ProjectSchema

    schema = await linked_data_dumpable.linked_data_schema(project)
    if schema.def_name:
        portable["$schema"] = await ProjectSchema.def_url(project, schema.def_name)


class LinkedDataDumpable(Generic[_PortableDataT]):
    """
    Describe an object that can be dumped to linked data.
    """

    @abstractmethod
    async def dump_linked_data(self, project: Project, /) -> _PortableDataT:
        """
        Dump this instance to `JSON-LD <https://json-ld.org/>`_.
        """


class LinkedDataDumpableWithSchema(
    Generic[_SchemaTypeT, _PortableDataT], LinkedDataDumpable[_PortableDataT]
):
    """
    Describe an object that can be dumped to linked data.
    """

    @classmethod
    @abstractmethod
    async def linked_data_schema(cls, project: Project, /) -> _SchemaTypeT:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.json.linked_data.LinkedDataDumpable.dump_linked_data`.
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
        self._schema["allOf"] = [JsonLdSchema().embed(self)]


class LinkedDataDumpableWithSchemaJsonLdObject(
    LinkedDataDumpableWithSchema[JsonLdObject, PortableMapping], ABC
):
    """
    A :py:class:`betty.json.linked_data.LinkedDataDumpable` implementation for object/mapping data.

    This is helpful when working with diamond class hierarchies where parent classes that may not be the root class want
    to make changes to the linked data, and expect an :py:class`betty.json.schema.Object` schema and a
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


class LinkedDataDumper(Generic[_T, _SchemaTypeT, _PortableDataT], ABC):
    """
    Provide linked data for instances of a target type.
    """

    @abstractmethod
    async def linked_data_schema_for(self, project: Project, /) -> _SchemaTypeT:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.json.linked_data.LinkedDataDumper.dump_linked_data_for`.
        """

    @abstractmethod
    async def dump_linked_data_for(
        self, project: Project, target: _T, /
    ) -> _PortableDataT:
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


@final
class JsonLdSchema(Singleton, Schema):
    """
    A `JSON-LD <https://json-ld.org/>`_ JSON Schema reference.
    """

    _SCHEMA: PortableMapping = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": True,
        "allOf": [
            {"$ref": "#/$defs/context"},
            {"$ref": "#/$defs/graph"},
            {"$ref": "#/$defs/common"},
        ],
        "$defs": {
            "context": {
                "additionalProperties": True,
                "properties": {
                    "@context": {
                        "description": "Used to define the short-hand names that are used throughout a JSON-LD document.",
                        "type": ["object", "string", "array", "null"],
                    }
                },
            },
            "graph": {
                "additionalProperties": True,
                "properties": {
                    "@graph": {
                        "description": "Used to express a graph.",
                        "anyOf": [
                            {"type": "array", "items": {"$ref": "#/$defs/common"}},
                            {"$ref": "#/$defs/common", "type": "object"},
                        ],
                    }
                },
            },
            "common": {
                "additionalProperties": {"anyOf": [{"$ref": "#/$defs/common"}]},
                "properties": {
                    "@id": {
                        "description": "Used to uniquely identify things that are being described in the document with IRIs or blank node identifiers.",
                        "type": "string",
                        "format": "uri",
                    },
                    "@value": {
                        "description": "Used to specify the data that is associated with a particular property in the graph.",
                        "type": ["string", "boolean", "number", "null"],
                    },
                    "@language": {
                        "description": "Used to specify the language for a particular string value or the default language of a JSON-LD document.",
                        "type": ["string", "null"],
                    },
                    "@type": {
                        "description": "Used to set the data type of a node or typed value.",
                        "type": ["string", "null", "array"],
                    },
                    "@container": {
                        "description": "Used to set the default container type for a term.",
                        "type": ["string", "null"],
                        "enum": ["@language", "@list", "@index", "@set"],
                    },
                    "@list": {"description": "Used to express an ordered set of data."},
                    "@set": {
                        "description": "Used to express an unordered set of data and to ensure that values are always represented as arrays."
                    },
                    "@reverse": {
                        "description": "Used to express reverse properties.",
                        "type": ["string", "object", "null"],
                        "additionalProperties": {"anyOf": [{"$ref": "#/$defs/common"}]},
                    },
                    "@base": {
                        "description": "Used to set the base IRI against which relative IRIs are resolved",
                        "type": ["string", "null"],
                        "format": "uri",
                    },
                    "@vocab": {
                        "description": "Used to expand properties and values in @type with a common prefix IRI",
                        "type": ["string", "null"],
                        "format": "uri",
                    },
                },
            },
        },
        "title": "Schema for JSON-LD",
        "type": ["object", "array"],
    }

    def __init__(self):
        super().__init__(def_name="jsonLd", title="JSON-LD")
        self._schema = self._SCHEMA
