"""
Tools for managing objects.
"""

from __future__ import annotations

from typing import Any, Final, final


@final
class AttrOperators[ObjectT]:
    """
    Implement ``hasattr()``, ``getattr()``, ``setattr()``, and ``delattr()``, but pre-fill the attribute name.
    """

    __slots__ = ("name",)

    def __init__(self, name: str, /):
        self.name: Final[str] = name
        """
        The attribute name.
        """

    def has(self, object_: ObjectT, /) -> bool:
        """
        Check if an attribute value is stored on the object.
        """
        return hasattr(object_, self.name)

    def get(self, object_: ObjectT, /) -> Any:
        """
        Get the attribute value from the object, if any.
        """
        return getattr(object_, self.name)

    def set(self, object_: ObjectT, value: Any, /) -> None:
        """
        Set the attribute value on the object.
        """
        setattr(object_, self.name, value)

    def delete(self, object_: ObjectT, /) -> None:
        """
        Delete the attribute value from the object, if any.
        """
        delattr(object_, self.name)
