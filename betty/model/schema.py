"""
JSON schemas for the model API.
"""

from __future__ import annotations

from betty.json.schema import Array, Null, OneOf, String


class ToZeroOrOneSchema(OneOf):
    """
    A schema for a to-zero-or-one entity association.
    """

    def __init__(self, *, title: str | None = None, description: str | None = None):
        super().__init__(
            String(
                title=title or "Optional associate entity",
                description=description
                or "An optional reference to an associate entity's JSON resource",
                format=String.Format.URI,
            ),
            Null(),
        )


class ToOneSchema(String):
    """
    A schema for a to-one entity association.
    """

    def __init__(self, *, title: str | None = None, description: str | None = None):
        super().__init__(
            title=title or "Associate entity",
            description=description
            or "A reference to an associate entity's JSON resource",
            format=String.Format.URI,
        )


class ToManySchema(Array):
    """
    A schema for a to-many entity association.
    """

    def __init__(self, *, title: str | None = None, description: str | None = None):
        super().__init__(
            ToOneSchema(),
            title=title or "Associate entities",
            description=description
            or "References to associate entities' JSON resources",
        )
