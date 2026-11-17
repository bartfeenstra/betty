"""
Abstract classes.
"""

from functools import wraps
from typing import Any


def abstract[ClsT](cls: type[ClsT], /) -> type[ClsT]:
    """
    Disallow a class from being initialized directly.
    """
    original_init = cls.__init__

    @wraps(original_init)
    def _init(self: ClsT, *args: Any, **kwargs: Any) -> None:
        if type(self) is cls:
            raise TypeError(
                f"{cls.__name__} cannot be initialized directly. Initialize one of its subclasses instead."
            )
        original_init(self, *args, **kwargs)

    cls.__init__ = _init  # ty: ignore[invalid-assignment]
    return cls
