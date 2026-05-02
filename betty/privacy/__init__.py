"""
The Privacy API.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, final

from betty.linked_data import (
    LinkedDataDumpableWithSchema as LinkedDataDumpableWithSchema,
)

if TYPE_CHECKING:
    from betty.json_schema import Schema as Schema
    from betty.portable import PortableMapping as PortableMapping
    from betty.project import Project as Project


@final
class Privacy(enum.Enum):
    """
    The available privacy modes.
    """

    PUBLIC = False
    """
    The resource is explicitly made public.
    """

    PRIVATE = True
    """
    The resource is explicitly made private.
    """

    UNDETERMINED = None
    """
    The resource has no explicit privacy. This means that:
    
    - it may be changed at will
    - when checking access, UNDETERMINED evaluates to PUBLIC.
    """
