from typing import Any, Iterable


def walk(item: Any, attribute_name: str) -> Iterable[Any]:
    children = getattr(item, attribute_name)

    # If the child has the requested attribute, yield it,
    if hasattr(children, attribute_name):
        yield children
        yield from walk(children, attribute_name)

    # Otherwise loop over the children and yield their attributes.
    try:
        children = iter(children)
    except TypeError:
        return
    for child in children:
        yield child
        yield from walk(child, attribute_name)
