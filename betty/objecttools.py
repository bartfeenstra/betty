"""
Tools for managing objects.
"""

from __future__ import annotations

from typing import Final, final, overload


@final
class AttrOperators[ObjectT, ValueT]:
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

    @overload
    def get(self, object_: ObjectT, /) -> ValueT:
        pass

    @overload
    def get(self, object_: ObjectT, default: ValueT, /) -> ValueT:
        pass

    def get(self, *args):
        """
        Get the attribute value from the object, if any.
        """
        match len(args):
            case 1:
                return getattr(args[0], self.name)
            case 2:
                return getattr(args[0], self.name, args[1])

    def set(self, object_: ObjectT, value: ValueT, /) -> None:
        """
        Set the attribute value on the object.
        """
        setattr(object_, self.name, value)

    def delete(self, object_: ObjectT, /) -> None:
        """
        Delete the attribute value from the object, if any.
        """
        delattr(object_, self.name)
