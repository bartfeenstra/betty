"""
Provide JSON utilities.
"""

from __future__ import annotations

import enum
from typing import Any, cast, final

from jsonschema.validators import Draft202012Validator
from referencing import Registry, Resource
from typing_extensions import override

from betty.classtools import Singleton
from betty.serde.dump import Dump, DumpMapping


class Schema:
    """
    A JSON Schema.

    All schemas using this class **MUST** follow JSON Schema Draft 2020-12.

    To test your own subclasses, use :py:class:`betty.test_utils.json.schema.SchemaTestBase`.
    """

    def __init__(
        self,
        *,
        def_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        self._def_name = def_name
        self._schema: DumpMapping[Dump] = {
            # The entire API assumes this dialect, so enforce it.
            "$schema": "https://json-schema.org/draft/2020-12/schema",
        }
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description

    @property
    def def_name(self) -> str | None:
        """
        The schema machine name when embedded into another schema's ``$defs``.
        """
        return self._def_name

    @property
    def schema(self) -> DumpMapping[Dump]:
        """
        The raw JSON Schema.
        """
        return self._schema

    @property
    def title(self) -> str | None:
        """
        The schema's human-readable US English (short) title.
        """
        try:
            return cast(str, self._schema["title"])
        except KeyError:
            return None

    @title.setter
    def title(self, title: str) -> None:
        self._schema["title"] = title

    @property
    def description(self) -> str | None:
        """
        The schema's human-readable US English (long) description.
        """
        try:
            return cast(str, self._schema["description"])
        except KeyError:
            return None

    @description.setter
    def description(self, description: str) -> None:
        self._schema["description"] = description

    @property
    def defs(self) -> DumpMapping[Dump]:
        """
        The JSON Schema's ``$defs`` definitions, kept separately, so they can be merged when this schema is embedded.

        Only top-level definitions are supported. You **MUST NOT** nest definitions. Instead, prefix or suffix
        their names.
        """
        return cast(DumpMapping[Dump], self._schema.setdefault("$defs", {}))

    def embed(self, into: Schema) -> DumpMapping[Dump]:
        """
        Embed this schema.

        This is where the raw schema may be enhanced before being returned.
        """
        for name, schema in self.defs.items():
            into.defs[name] = schema
        schema = {
            child_name: child_schema
            for child_name, child_schema in self.schema.items()
            if child_name not in ("$defs", "$schema")
        }
        if self._def_name is None:
            return schema
        into.defs[self._def_name] = schema
        return Ref(self._def_name).embed(into)

    def validate(self, data: Any) -> None:
        """
        Validate data against this schema.
        """
        schema = self.schema
        if "$id" not in schema:
            schema["$id"] = "https://betty.example.com"
        schema_registry = Resource.from_contents(schema) @ Registry()
        validator = Draft202012Validator(
            schema,
            registry=schema_registry,
        )
        validator.validate(data)


class _Type(Schema):
    _type: str

    def __init__(
        self,
        *,
        def_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        super().__init__(def_name=def_name, title=title, description=description)
        self._schema["type"] = self._type


class String(_Type):
    """
    A JSON Schema ``string`` type.
    """

    _type = "string"

    class Format(enum.Enum):
        """
        A JSON Schema ``string`` type's ``format``.
        """

        DATE_TIME = "date-time"
        TIME = "time"
        DATE = "date"
        DURATION = "duration"
        EMAIL = "email"
        IDN_EMAIL = "idn-email"
        HOSTNAME = "hostname"
        IDN_HOSTNAME = "idn-hostname"
        IPV4 = "ipv4"
        IPV6 = "ipv6"
        UUID = "uuid"
        URI = "uri"
        URI_REFERENCE = "uri-reference"
        IRI = "iri"
        IRI_REFERENCE = "iri-reference"
        URI_TEMPLATE = "uri-template"
        JSON_POINTER = "json-pointer"
        RELATIVE_JSON_POINTER = "relative-json-pointer"
        REGEX = "regex"

    def __init__(
        self,
        *,
        def_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        format: Format | None = None,  # noqa A002
    ):
        super().__init__(
            def_name=def_name,
            title=title,
            description=description,
        )
        if min_length is not None:
            self._schema["minLength"] = min_length
        if max_length is not None:
            self._schema["maxLength"] = max_length
        if pattern is not None:
            self._schema["pattern"] = pattern
        if format is not None:
            self._schema["format"] = format.value


class Boolean(_Type):
    """
    A JSON Schema ``boolean`` type.
    """

    _type = "boolean"


class Number(_Type):
    """
    A JSON Schema ``number`` type.
    """

    _type = "number"


class Integer(_Type):
    """
    A JSON Schema ``integer`` type.
    """

    _type = "integer"


class Null(_Type):
    """
    A JSON Schema ``null`` type.
    """

    _type = "null"


class Object(_Type):
    """
    A JSON Schema ``object`` type.
    """

    _type = "object"

    def __init__(
        self,
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
        self._properties = self._schema["properties"] = {}
        self._required = self._schema["required"] = []

    def add_property(
        self,
        property_name: str,
        property_schema: Schema,
        property_required: bool = True,
    ) -> None:
        """
        Add a property to the object schema.
        """
        self._properties[property_name] = property_schema.embed(self)
        if property_required:
            self._required.append(property_name)


class Array(_Type):
    """
    A JSON Schema ``array`` type.
    """

    _type = "array"

    def __init__(
        self,
        items: Schema,
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
        self._schema["items"] = items.embed(self)


class _Container(Schema):
    _type: str

    def __init__(
        self,
        *items: Schema,
        def_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        super().__init__(def_name=def_name, title=title, description=description)
        self._schema[self._type] = [item.embed(self) for item in items]


class AllOf(_Container):
    """
    A JSON Schema ``allOf``.
    """

    _type = "allOf"


class AnyOf(_Container):
    """
    A JSON Schema ``anyOf``.
    """

    _type = "anyOf"


class OneOf(_Container):
    """
    A JSON Schema ``oneOf``.
    """

    _type = "oneOf"


class Const(Schema):
    """
    A JSON Schema ``const``.
    """

    def __init__(
        self,
        const: Dump,
        *,
        def_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        super().__init__(def_name=def_name, title=title, description=description)
        self._schema["const"] = const


class Enum(Schema):
    """
    A JSON Schema ``enum``.
    """

    def __init__(
        self,
        *values: Dump,
        def_name: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ):
        super().__init__(def_name=def_name, title=title, description=description)
        self._schema["enum"] = list(values)


class Def(str):
    """
    The name of a named Betty schema.

    Using this instead of :py:class:`str` directly allows Betty to
    bundle schemas together under a project namespace.

    See :py:attr:`betty.json.schema.Schema.def_name`.
    """

    __slots__ = ()

    @override
    def __new__(cls, def_name: str):
        return super().__new__(cls, f"#/$defs/{def_name}")


class Ref(Schema):
    """
    A JSON Schema that references a named Betty schema.
    """

    def __init__(self, def_name: str):
        super().__init__()
        self._schema["$ref"] = Def(def_name)


class JsonSchemaReference(String):
    """
    The JSON Schema schema.
    """

    def __init__(self):
        super().__init__(
            def_name="jsonSchemaReference",
            title="JSON Schema reference",
            format=String.Format.URI,
            description="A JSON Schema URI.",
        )


@final
class JsonSchemaSchema(Singleton, Schema):
    """
    The JSON Schema Draft 2020-12 schema.
    """

    _SCHEMA: DumpMapping[Dump] = {
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

    def __init__(self):
        super().__init__(def_name="jsonSchema", title="JSON Schema")
        self._schema = self._SCHEMA
