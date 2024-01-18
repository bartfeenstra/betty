"""
Provide class utilities.
"""
from typing import Any


def repr_instance(instance: object, **attributes: Any) -> str:
    """
    Build a representation of an instance.
    """
    return '<{}.{} object at {}; {}>'.format(
        instance.__class__.__module__,
        instance.__class__.__name__,
        hex(id(instance)),
        (' ' + ', '.join(map(lambda x: f'{x[0]}={x[1]}', attributes.items()))).rstrip(),
    )
