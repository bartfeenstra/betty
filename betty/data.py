"""
Data management and description.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.locale.localizable import Chain, Localizable
from betty.locale.localized import LocalizedStr

if TYPE_CHECKING:
    import pathlib
    from collections.abc import MutableSequence, Sequence

    from betty.locale.localized import Localized
    from betty.locale.localizer import Localizer


class Context(Localizable):
    """
    Describe a location of a piece of data.
    """


class Selector(Context):
    """
    Describe a nested piece of data relative to the total data.
    """


@final
class Selectors(Context):
    """
    Combine multiple selector contexts into a single selector.
    """

    def __init__(self, *selectors: Selector):
        self._selectors = list(selectors)

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return Chain("data", *self._selectors).localize(localizer)

    @classmethod
    def reduce(cls, *contexts: Context) -> Sequence[Context]:
        """
        Reduce all consecutive instances of py:class:`betty.data.Selector` to a single instance of this class.

        All other contexts are kept verbatim.
        """
        reduced_contexts: MutableSequence[Context] = []
        for context in contexts:
            if isinstance(context, Selector):
                try:
                    last_context = reduced_contexts[-1]
                except IndexError:
                    pass
                else:
                    if isinstance(last_context, Selectors):
                        last_context._selectors.append(context)
                        continue
                reduced_contexts.append(Selectors(context))
            else:
                reduced_contexts.append(context)
        return reduced_contexts


@final
class Attr(Selector):
    """
    An object attribute context.
    """

    def __init__(self, attr: str):
        self._attr = attr

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return LocalizedStr(f".{self._attr}")


@final
class Index(Selector):
    """
    A sequence index context.
    """

    def __init__(self, index: int):
        self._index = index

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return LocalizedStr(f"[{self._index}]")


@final
class Key(Selector):
    """
    A mapping key context.
    """

    def __init__(self, key: str):
        self._key = key

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return LocalizedStr(f'["{self._key}"]')


@final
class Path(Context):
    """
    A file on disk.
    """

    def __init__(self, path: pathlib.Path):
        self._path = path

    @override
    def localize(self, localizer: Localizer) -> Localized & str:
        return LocalizedStr(str(self._path))
