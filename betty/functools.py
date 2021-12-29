from typing import Any, Iterable, Sized


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


def slice_to_range(ranged_slice: slice, iterable: Sized) -> Iterable[int]:
    return range(
        0 if ranged_slice.start is None else ranged_slice.start,
        len(iterable) if ranged_slice.stop is None else ranged_slice.stop,
        1 if ranged_slice.step is None else ranged_slice.step,
    )
