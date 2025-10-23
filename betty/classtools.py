"""
Tools to create classes.
"""

from typing import Any, Self

from typing_extensions import override


class Singleton:
    """
    A base class for singletons.
    """

    _instance: Self | None = None

    @override
    def __new__(cls, *args: Any, **kwargs: Any):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, *kwargs)
        return cls._instance
