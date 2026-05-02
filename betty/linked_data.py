"""
Provide `JSON-LD <https://json-ld.org/>`_ utilities.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Final

from betty.portable import PortableData, PortableMapping

if TYPE_CHECKING:
    from betty.json_schema import Schema
    from betty.project import Project


class LinkedDataDumpable[PortableDataT: PortableData = PortableData](ABC):
    """
    Describe an object that can be dumped to linked data.
    """

    @abstractmethod
    async def dump_linked_data(self, project: Project, /) -> PortableDataT:
        """
        Dump this instance to `JSON-LD <https://json-ld.org/>`_.
        """


class LinkedDataDumpableWithSchema[PortableDataT: PortableData = PortableData](
    LinkedDataDumpable[PortableDataT]
):
    """
    Describe an object that can be dumped to linked data.
    """

    @classmethod
    @abstractmethod
    async def linked_data_schema(cls, project: Project, /) -> Schema:
        """
        Define the `JSON Schema <https://json-schema.org/>`_ for :py:meth:`betty.linked_data.LinkedDataDumpable.dump_linked_data`.
        """


class LinkedDataDumper[T, PortableDataT: PortableData = PortableData](ABC):
    """
    Provide linked data for instances of a target type.
    """

    @abstractmethod
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
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


JSON_LD_SCHEMA: Final[PortableMapping] = {
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
"""
A `JSON-LD <https://json-ld.org/>`_ JSON Schema reference.
"""
