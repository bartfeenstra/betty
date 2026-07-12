"""
Multi-threading support.
"""

from __future__ import annotations

from betty.docstring import append


def threadsafe[T](target: T, /) -> T:
    """
    Mark a target as thread-safe.
    """
    attr_name = "_betty_threading_threadsafe"
    if not hasattr(target, attr_name):
        target.__doc__ = append(
            target.__doc__ or "",
            "This is thread-safe, which means you can safely use this between different threads.",
        )
        setattr(target, attr_name, True)
    return target
