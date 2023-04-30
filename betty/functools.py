from typing import Any, Iterable, Sized, TypeVar, Callable, Type, Iterator

T = TypeVar('T')


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


def slice_to_range(indices: slice, iterable: Sized) -> Iterable[int]:
    length = len(iterable)

    if indices.start is None:
        start = 0
    else:
        # Ensure the stop index is within range.
        start = max(-length, min(length, indices.start))

    if indices.stop is None:
        stop = max(0, length)
    else:
        # Ensure the stop index is within range.
        stop = max(-length, min(length, indices.stop))

    if indices.step is None:
        step = 1
    else:
        step = indices.step

    return range(start, stop, step)


def filter_suppress(raising_filter: Callable[[T], Any], exception_type: Type[BaseException], items: Iterable[T]) -> Iterator[T]:
    for item in items:
        try:
            raising_filter(item)
            yield item
        except exception_type:
            continue
