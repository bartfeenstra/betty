"""
Test utilities for :py:mod:`betty.linked_data`.
"""

from betty.json_schema import validate as validate_json_schema
from betty.linked_data import LinkedData
from betty.portable import PortableMapping
from betty.typing import Void, Voidable, VoidableType, VoidType


def validate(
    schema: VoidableType[PortableMapping] | bool, data: LinkedData | VoidType, /
) -> None:
    """
    Validate linked data against a schema.

    :raises ValidationError:
    """
    if isinstance(schema, Voidable):
        if data is Void:
            return
        schema = schema.wrapped
    assert data is not Void, (
        "Data is unexpectedly void, and the schema does not allow this."
    )

    validate_json_schema(schema, data.data)
