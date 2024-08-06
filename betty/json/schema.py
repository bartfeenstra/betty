"""
Provide JSON utilities.
"""

from __future__ import annotations

from collections.abc import MutableSequence
from json import loads
from pathlib import Path
from typing import Any, Self, cast

import aiofiles
from betty.serde.dump import DumpMapping, Dump
from jsonschema.validators import Draft202012Validator
from referencing import Resource, Registry
from typing_extensions import override


class Schema:
    """
    A JSON Schema.

    All schemas using this class **MUST** follow JSON Schema Draft 2020-12.

    To test your own subclasses, use :py:class:`betty.test_utils.json.schema.SchemaTestBase`.
    """

    def __init__(
        self, *, def_name: str | None = None, schema: DumpMapping[Dump] | None = None
    ):
        self._def_name = def_name
        self._schema = schema or {}

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
        schema = {
            **self._schema,
            # The entire API assumes this dialect, so enforce it.
            "$schema": "https://json-schema.org/draft/2020-12/schema",
        }
        return schema

    @property
    def defs(self) -> DumpMapping[Dump]:
        """
        The JSON Schema's ``$defs`` definitions, kept separately, so they can be merged when this schema is embedded.

        Only top-level definitions are supported. You **MUST NOT** nest definitions. Instead, prefix or suffix
        their names.
        """
        return cast(DumpMapping[Dump], self._schema.setdefault("$defs", {}))

    def embed(self, into: Schema) -> Dump:
        """
        Embed this schema.
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
        schema_registry = Resource.from_contents(schema) @ Registry()  # type: ignore[operator, var-annotated]
        validator = Draft202012Validator(
            schema,
            registry=schema_registry,
        )
        validator.validate(data)


class ArraySchema(Schema):
    """
    A JSON Schema array.
    """

    def __init__(self, items_schema: Schema, *, def_name: str | None = None):
        super().__init__(def_name=def_name)
        self._schema["type"] = "array"
        self._schema["items"] = items_schema.embed(self)


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
        super().__init__(schema={"$ref": Def(def_name)})


def add_property(
    into: Schema,
    property_name: str,
    property_schema: Schema,
    property_required: bool = True,
) -> None:
    """
    Add a property to an object schema.
    """
    into._schema["type"] = "object"
    schema_properties = cast(
        DumpMapping[Dump], into._schema.setdefault("properties", {})
    )
    schema_properties[property_name] = property_schema.embed(into)
    if property_required:
        schema_required = cast(
            MutableSequence[str], into._schema.setdefault("required", [])
        )
        schema_required.append(property_name)


class JsonSchemaReference(Schema):
    """
    The JSON Schema schema.
    """

    def __init__(self):
        super().__init__(
            def_name="jsonSchemaReference",
            schema={
                "type": "string",
                "format": "uri",
                "description": "A JSON Schema URI.",
            },
        )


class FileBasedSchema(Schema):
    """
    A JSON Schema that is stored in a file.
    """

    @classmethod
    async def new_for(cls, file_path: Path, *, name: str | None = None) -> Self:
        """
        Create a new instance.
        """
        async with aiofiles.open(file_path) as f:
            raw_schema = await f.read()
        return cls(def_name=name, schema=loads(raw_schema))


class JsonSchemaSchema(FileBasedSchema):
    """
    The JSON Schema Draft 2020-12 schema.
    """

    @classmethod
    async def new(cls) -> Self:
        """
        Create a new instance.
        """
        return await cls.new_for(
            Path(__file__).parent / "schemas" / "json-schema.json", name="jsonSchema"
        )
