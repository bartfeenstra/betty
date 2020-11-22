from typing import Any, Iterable


def walk(item: Any, attribute_name: str) -> Iterable[Any]:
    child = getattr(item, attribute_name)

    # If the child has the requested attribute, yield it,
    if hasattr(child, attribute_name):
        yield child
        yield from walk(child, attribute_name)

    # Otherwise loop over the children and yield their attributes.
    try:
        child = iter(child)
    except TypeError:
        return
    for child in child:
        yield child
        yield from walk(child, attribute_name)
