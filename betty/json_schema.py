"""
Provide JSON utilities.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any, Final, cast, override

from jsonschema.validators import Draft202012Validator
from referencing import Registry, Resource

from betty.locale.localize import default_localizer, resolve_localized
from betty.portable import PortableData, PortableMapping

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable


class Schema:
    """
    A JSON Schema.

    All schemas using this class **MUST** follow JSON Schema Draft 2020-12.

    To test your own subclasses, use :py:class:`betty.test_utils.json_schema.SchemaTestBase`.
    """

    def __init__(
        self,
        *,
        def_name: str | None = None,
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        self._def_name = def_name
        self.schema: Final[PortableMapping] = {
            # The entire API assumes this dialect, so enforce it.
            "$schema": "https://json-schema.org/draft/2020-12/schema",
        }
        """
        The raw JSON Schema.
        """
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
    def title(self) -> str | None:
        """
        The schema's human-readable US English (short) title.
        """
        try:
            return cast(str, self.schema["title"])
        except KeyError:
            return None

    @title.setter
    def title(self, title: ResolvableLocalizable) -> None:
        self.schema["title"] = resolve_localized(title, localizer=default_localizer)

    @property
    def description(self) -> str | None:
        """
        The schema's human-readable US English (long) description.
        """
        try:
            return cast(str, self.schema["description"])
        except KeyError:
            return None

    @description.setter
    def description(self, description: ResolvableLocalizable) -> None:
        self.schema["description"] = resolve_localized(
            description, localizer=default_localizer
        )

    @property
    def defs(self) -> PortableMapping:
        """
        The JSON Schema's ``$defs`` definitions, kept separately, so they can be merged when this schema is embedded.

        Only top-level definitions are supported. You **MUST NOT** nest definitions. Instead, prefix or suffix
        their names.
        """
        return cast(PortableMapping, self.schema.setdefault("$defs", {}))

    def embed(self, into: Schema, /) -> PortableMapping:
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
        if self.def_name is None:
            return schema
        into.defs[self.def_name] = schema
        return Ref(self.def_name).embed(into)

    def validate(self, data: Any, /) -> None:
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
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(def_name=def_name, title=title, description=description)
        self.schema["type"] = self._type


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
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        format: Format | None = None,  # noqa: A002
    ):
        super().__init__(
            def_name=def_name,
            title=title,
            description=description,
        )
        if min_length is not None:
            self.schema["minLength"] = min_length
        if max_length is not None:
            self.schema["maxLength"] = max_length
        if pattern is not None:
            self.schema["pattern"] = pattern
        if format is not None:
            self.schema["format"] = format.value


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
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            def_name=def_name,
            title=title,
            description=description,
        )
        self._properties = self.schema["properties"] = {}
        self._required = self.schema["required"] = []

    def add_property(
        self,
        property_name: str,
        property_schema: Schema,
        property_required: bool = True,
        /,
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
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            def_name=def_name,
            title=title,
            description=description,
        )
        self.schema["items"] = items.embed(self)


class _Container(Schema):
    _type: str

    def __init__(
        self,
        *items: Schema,
        def_name: str | None = None,
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(def_name=def_name, title=title, description=description)
        self.schema[self._type] = [item.embed(self) for item in items]


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
        const: PortableData,
        *,
        def_name: str | None = None,
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(def_name=def_name, title=title, description=description)
        self.schema["const"] = const


class Enum(Schema):
    """
    A JSON Schema ``enum``.
    """

    def __init__(
        self,
        *values: PortableData,
        def_name: str | None = None,
        title: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(def_name=def_name, title=title, description=description)
        self.schema["enum"] = list(values)


class Def(str):
    """
    The name of a named Betty schema.

    Using this instead of :py:class:`str` directly allows Betty to
    bundle schemas together under a project namespace.

    See :py:attr:`betty.json_schema.Schema.def_name`.
    """

    __slots__ = ()

    @override
    def __new__(cls, def_name: str, /):
        return super().__new__(cls, f"#/$defs/{def_name}")


class Ref(Schema):
    """
    A JSON Schema that references a named Betty schema.
    """

    def __init__(self, def_name: str, /):
        super().__init__()
        self.schema["$ref"] = Def(def_name)


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
