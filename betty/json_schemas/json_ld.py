"""
JSON Schemas for JSON-LD.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, final

from betty.json_schema import Schema

if TYPE_CHECKING:
    from betty.portable import PortableMapping


@final
class JsonLdSchema(Schema):
    """
    A `JSON-LD <https://json-ld.org/>`_ JSON Schema reference.
    """

    _SCHEMA: ClassVar[PortableMapping] = {
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
