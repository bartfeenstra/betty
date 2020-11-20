from typing import Any, Iterable


def walk_to_many(item: Any, attribute_name: str) -> Iterable[Any]:
    for child in getattr(item, attribute_name):
        yield child
        yield from walk_to_many(child, attribute_name)
