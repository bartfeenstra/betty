"""
Providing typing utilities.
"""

import re
from typing import TypeVar


_T = TypeVar("_T")


_INTERNAL_INDENTATION_PATTERN = re.compile(r"( +)")


def _internal(target: _T) -> _T:
    doc = target.__doc__ or ""
    doc_last_line = doc.rsplit("\n")[-1]
    indentation_match = _INTERNAL_INDENTATION_PATTERN.match(doc_last_line)
    indentation = indentation_match.group(0) if indentation_match else ""
    target.__doc__ = (
        doc
        + f"\n\n{indentation}This is internal. It **MAY** be used anywhere in Betty's source code, but **MUST NOT** be used by third-party code."
    )
    return target


@_internal
def internal(target: _T) -> _T:
    """
    Mark a target as internal to Betty.

    Anything decorated with ``@internal`` MAY be used anywhere in Betty's source code,
    but MUST be considered private by third-party code.
    """
    return _internal(target)


@internal
def public(target: _T) -> _T:
    """
    Mark a target as publicly usable.

    This is intended for items nested inside something marked with :py:func:`betty.typing.internal`,
    such as class attributes: third-party code **SHOULD NOT** use a class marked ``@internal``
    directly, but **MAY** use any of its attributes that are marked ``@public``.
    """
    return target
