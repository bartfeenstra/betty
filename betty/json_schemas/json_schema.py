"""
JSON Schemas for JSON Schema.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from betty.portable import PortableMapping

json_schema_schema: Final[PortableMapping] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://json-schema.org/draft/2020-12/schema",
    "$vocabulary": {
        "https://json-schema.org/draft/2020-12/vocab/core": True,
        "https://json-schema.org/draft/2020-12/vocab/applicator": True,
        "https://json-schema.org/draft/2020-12/vocab/unevaluated": True,
        "https://json-schema.org/draft/2020-12/vocab/validation": True,
        "https://json-schema.org/draft/2020-12/vocab/meta-data": True,
        "https://json-schema.org/draft/2020-12/vocab/format-annotation": True,
        "https://json-schema.org/draft/2020-12/vocab/content": True,
    },
    "$dynamicAnchor": "meta",
    "title": "Core and Validation specifications meta-schema",
    "allOf": [
        {"$ref": "meta/core"},
        {"$ref": "meta/applicator"},
        {"$ref": "meta/unevaluated"},
        {"$ref": "meta/validation"},
        {"$ref": "meta/meta-data"},
        {"$ref": "meta/format-annotation"},
        {"$ref": "meta/content"},
    ],
    "type": ["object", "boolean"],
    "$comment": "This meta-schema also defines keywords that have appeared in previous drafts in order to prevent incompatible extensions as they remain in common use.",
    "properties": {
        "definitions": {
            "$comment": '"definitions" has been replaced by "$defs".',
            "type": "object",
            "additionalProperties": {"$dynamicRef": "#meta"},
            "deprecated": True,
            "default": {},
        },
        "dependencies": {
            "$comment": '"dependencies" has been split and replaced by "dependentSchemas" and "dependentRequired" in order to serve their differing semantics.',
            "type": "object",
            "additionalProperties": {
                "anyOf": [
                    {"$dynamicRef": "#meta"},
                    {"$ref": "meta/validation#/$defs/stringArray"},
                ]
            },
            "deprecated": True,
            "default": {},
        },
        "$recursiveAnchor": {
            "$comment": '"$recursiveAnchor" has been replaced by "$dynamicAnchor".',
            "$ref": "meta/core#/$defs/anchorString",
            "deprecated": True,
        },
        "$recursiveRef": {
            "$comment": '"$recursiveRef" has been replaced by "$dynamicRef".',
            "$ref": "meta/core#/$defs/uriReferenceString",
            "deprecated": True,
        },
    },
}
"""
The JSON Schema Draft 2020-12 schema.
"""
