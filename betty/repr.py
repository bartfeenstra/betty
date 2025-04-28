"""
Provide utilities to represent values as strings.
"""

from typing import Any


def repr_instance(instance: object, **attributes: Any) -> str:
    """
    Build a representation of an instance.
    """
    return "<{}.{} object at {}; {}>".format(
        instance.__class__.__module__,
        instance.__class__.__name__,
        hex(id(instance)),
        (" " + ", ".join(f"{x[0]}={x[1]}" for x in attributes.items())).rstrip(),
    )
