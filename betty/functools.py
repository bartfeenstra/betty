from __future__ import annotations

from typing import Any, Iterable, Sized, TypeVar, Callable, Iterator, Generic, cast

T = TypeVar('T')
U = TypeVar('U')


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


class _Result(Generic[T]):
    def __init__(self, value: T | None, _error: BaseException | None = None):
        assert not _error or value is None
        self._value = value
        self._error = _error

    @property
    def value(self) -> T:
        if self._error:
            raise self._error
        return cast(T, self._value)

    def map(self, f: Callable[[T], U]) -> _Result[U]:
        if self._error:
            return cast(_Result[U], self)
        try:
            return _Result(f(self.value))
        except BaseException as e:
            return _Result(None, e)


def filter_suppress(raising_filter: Callable[[T], Any], exception_type: type[BaseException], items: Iterable[T]) -> Iterator[T]:
    for item in items:
        try:
            raising_filter(item)
            yield item
        except exception_type:
            continue
