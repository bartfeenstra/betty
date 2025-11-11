"""
Tools to create classes.
"""

from typing import Self, final

from typing_extensions import override


class Singleton:
    """
    A base class for singletons.
    """

    _instance: Self | None = None

    @final
    @override
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
