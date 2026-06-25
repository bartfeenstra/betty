"""
Test utilities for :py:mod:`betty.linked_data`.
"""

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
        schema = schema.wrapped
    else:
        assert data is not Void, (
            "Data is unexpectedly void, and the schema does not allow this."
        )
    validate(schema, data)
