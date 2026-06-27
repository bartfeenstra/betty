"""
The Privacy API.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import final


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


class HasPrivacy(ABC):
    """
    Data that that has privacy.
    """

    @property
    @abstractmethod
    def privacy(self) -> Privacy:
        """
        The data's privacy.
        """
